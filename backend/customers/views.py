from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from common.permissions import IsAdminOrBranchManagerOrReadOnly
from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminOrBranchManagerOrReadOnly,
    ]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    filterset_fields = ["branch", "assigned_agent", "is_active"]
    search_fields = ["customer_code", "full_name", "phone", "email"]
    ordering_fields = ["full_name", "created_at", "customer_code"]
    ordering = ["full_name"]

    def get_queryset(self):
        user = self.request.user

        queryset = Customer.objects.select_related(
            "branch",
            "assigned_agent",
        )

        if user.is_superuser or user.role in {
            User.Role.ADMIN,
            User.Role.AUDITOR,
        }:
            return queryset

        if user.branch_id is None:
            return queryset.none()

        queryset = queryset.filter(branch_id=user.branch_id)

        if user.role == User.Role.BRANCH_MANAGER:
            return queryset

        if user.role == User.Role.COLLECTION_AGENT:
            return queryset.filter(assigned_agent=user)

        return queryset.none()