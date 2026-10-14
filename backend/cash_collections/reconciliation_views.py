
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import BankDeposit
from .reconciliation_serializers import (
    BankDepositCreateSerializer,
    BankDepositSerializer,
    MarkBankDepositSerializer,
    ReconcileCompanyAccountSerializer,
)
from .reconciliation_services import (
    create_bank_deposit,
    is_admin,
    mark_bank_deposit_complete,
    reconcile_company_account,
)


class BankDepositViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        queryset = (
            BankDeposit.objects.select_related("branch", "created_by")
            .prefetch_related("items__submission")
            .select_related("reconciliation")
        )

        if is_admin(user) or user.role == user.Role.AUDITOR:
            return queryset

        if user.role == user.Role.BRANCH_MANAGER:
            return queryset.filter(branch_id=user.branch_id)

        return queryset.none()

    def get_serializer_class(self):
        if self.action == "create":
            return BankDepositCreateSerializer
        if self.action == "mark_deposited":
            return MarkBankDepositSerializer
        if self.action == "reconcile":
            return ReconcileCompanyAccountSerializer
        return BankDepositSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        deposit = create_bank_deposit(
            submission_ids=serializer.validated_data["submission_ids"],
            created_by=request.user,
        )

        return Response(
            BankDepositSerializer(
                deposit,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="mark-deposited")
    def mark_deposited(self, request, pk=None):
        deposit = self.get_object()

        if not (
            is_admin(request.user)
            or request.user.role == request.user.Role.BRANCH_MANAGER
        ):
            raise PermissionDenied(
                "Only administrators or branch managers can record deposits."
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        deposit = mark_bank_deposit_complete(
            deposit_id=deposit.pk,
            updated_by=request.user,
            **serializer.validated_data,
        )

        return Response(
            BankDepositSerializer(
                deposit,
                context=self.get_serializer_context(),
            ).data
        )

    @action(detail=True, methods=["post"], url_path="reconcile")
    def reconcile(self, request, pk=None):
        deposit = self.get_object()

        if not is_admin(request.user):
            raise PermissionDenied(
                "Only administrators can reconcile company-account credits."
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reconciliation = reconcile_company_account(
            deposit_id=deposit.pk,
            reconciled_by=request.user,
            **serializer.validated_data,
        )

        deposit.refresh_from_db()

        return Response({
            "deposit": BankDepositSerializer(
                deposit,
                context=self.get_serializer_context(),
            ).data,
            "reconciliation": {
                "id": reconciliation.id,
                "statement_reference": reconciliation.statement_reference,
                "credited_amount": str(reconciliation.credited_amount),
                "status": reconciliation.status,
                "notes": reconciliation.notes,
            },
        })
