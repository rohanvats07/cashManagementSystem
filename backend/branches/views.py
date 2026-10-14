from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from branches.models import Branch
from branches.serializers import BranchSerializer
from common.permissions import IsAdminOrReadOnly


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    filterset_fields = ["is_active", "city", "state"]
    search_fields = ["code", "name", "city", "state"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        user = self.request.user

        queryset = Branch.objects.all()

        if user.is_superuser or user.role in {
            user.Role.ADMIN,
            user.Role.AUDITOR,
        }:
            return queryset

        if user.branch_id is None:
            return queryset.none()

        return queryset.filter(pk=user.branch_id)