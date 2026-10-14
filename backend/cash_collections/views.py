
from django.db.models import Sum
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CashCollection, CashSubmission
from .serializers import (
    CashCollectionCreateSerializer,
    CashCollectionSerializer,
    CashSubmissionCreateSerializer,
    CashSubmissionReviewSerializer,
    CashSubmissionSerializer,
)
from .services import (
    record_cash_collection,
    review_cash_submission,
    submit_collected_cash,
)


def is_admin(user):
    return user.is_superuser or user.role == user.Role.ADMIN


class CashCollectionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        queryset = CashCollection.objects.select_related(
            "loan",
            "customer",
            "collected_by",
        ).prefetch_related("allocations__schedule")

        if is_admin(user) or user.role == user.Role.AUDITOR:
            return queryset

        if user.role == user.Role.BRANCH_MANAGER:
            return queryset.filter(customer__branch_id=user.branch_id)

        if user.role == user.Role.COLLECTION_AGENT:
            return queryset.filter(collected_by=user)

        return queryset.none()

    def get_serializer_class(self):
        if self.action == "create":
            return CashCollectionCreateSerializer
        return CashCollectionSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role != request.user.Role.COLLECTION_AGENT:
            raise PermissionDenied(
                "Only collection agents can record cash collections."
            )

        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        collection = record_cash_collection(
            loan_id=data["loan"].pk,
            amount=data["amount"],
            collected_by=request.user,
            idempotency_key=data["idempotency_key"],
            collection_date=data.get("collection_date"),
            notes=data.get("notes", ""),
        )

        output = CashCollectionSerializer(
            collection,
            context=self.get_serializer_context(),
        )
        return Response(output.data, status=status.HTTP_201_CREATED)


class CashSubmissionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        queryset = CashSubmission.objects.select_related(
            "branch",
            "submitted_by",
            "reviewed_by",
        ).prefetch_related("items__collection")

        if is_admin(user) or user.role == user.Role.AUDITOR:
            return queryset

        if user.role == user.Role.BRANCH_MANAGER:
            return queryset.filter(branch_id=user.branch_id)

        if user.role == user.Role.COLLECTION_AGENT:
            return queryset.filter(submitted_by=user)

        return queryset.none()

    def get_serializer_class(self):
        if self.action == "create":
            return CashSubmissionCreateSerializer
        if self.action == "review":
            return CashSubmissionReviewSerializer
        return CashSubmissionSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role != request.user.Role.COLLECTION_AGENT:
            raise PermissionDenied(
                "Only collection agents can submit collected cash."
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = submit_collected_cash(
            collection_ids=serializer.validated_data["collection_ids"],
            submitted_by=request.user,
        )

        return Response(
            CashSubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        submission = self.get_object()

        if not (
            is_admin(request.user)
            or request.user.role == request.user.Role.BRANCH_MANAGER
            or request.user.is_superuser
        ):
            raise PermissionDenied(
                "Only administrators or branch managers can review submissions."
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = review_cash_submission(
            submission_id=submission.pk,
            reviewed_by=request.user,
            decision=serializer.validated_data["decision"],
            review_notes=serializer.validated_data.get("review_notes", ""),
        )

        return Response(
            CashSubmissionSerializer(submission).data,
            status=status.HTTP_200_OK,
        )
