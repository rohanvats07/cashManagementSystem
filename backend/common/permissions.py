from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.models import User


class IsCMRSAdmin(BasePermission):
    """Allow access only to CMRS administrators."""

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.role == User.Role.ADMIN)
        )


class IsAdminOrReadOnly(BasePermission):
    """Allow authenticated reads, but restrict writes to administrators."""

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return user.is_superuser or user.role == User.Role.ADMIN

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.is_superuser or user.role == User.Role.ADMIN:
            return True

        if request.method not in SAFE_METHODS:
            return False

        if user.role == User.Role.AUDITOR:
            return True

        return getattr(user, "branch_id", None) == obj.pk

class IsAdminOrBranchManagerOrReadOnly(BasePermission):
    """
    Permit writes to administrators and branch managers.
    Other authenticated roles receive read-only access.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return bool(
            user.is_superuser
            or user.role in {
                User.Role.ADMIN,
                User.Role.BRANCH_MANAGER,
            }
        )