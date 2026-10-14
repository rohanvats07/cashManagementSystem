from django.db.models import Count
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from common.permissions import IsAdminOrBranchManagerOrReadOnly
from loans.models import Loan
from loans.serializers import LoanSerializer, RepaymentScheduleSerializer


class LoanViewSet(
    mixins.CreateModelMixin,
    viewsets.ReadOnlyModelViewSet,
):
    serializer_class = LoanSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminOrBranchManagerOrReadOnly,
    ]

    filterset_fields = ["status", "customer"]
    search_fields = [
        "loan_number",
        "customer__customer_code",
        "customer__full_name",
        "customer__phone",
    ]
    ordering_fields = [
        "created_at",
        "disbursement_date",
        "principal_amount",
        "loan_number",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        queryset = Loan.objects.select_related(
            "customer",
            "customer__branch",
            "created_by",
        ).annotate(
            schedule_count=Count("repayment_schedules")
        )

        if user.is_superuser or user.role in {
            User.Role.ADMIN,
            User.Role.AUDITOR,
        }:
            return queryset

        if user.branch_id is None:
            return queryset.none()

        queryset = queryset.filter(customer__branch_id=user.branch_id)

        if user.role == User.Role.BRANCH_MANAGER:
            return queryset

        if user.role == User.Role.COLLECTION_AGENT:
            return queryset.filter(customer__assigned_agent=user)

        return queryset.none()

    @action(detail=True, methods=["get"], url_path="schedule")
    def schedule(self, request, pk=None):
        loan = self.get_object()

        schedules = loan.repayment_schedules.all()

        serializer = RepaymentScheduleSerializer(
            schedules,
            many=True,
        )

        return Response(serializer.data, status=status.HTTP_200_OK)