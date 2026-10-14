from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import User


@admin.register(User)
class CMRSUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "branch",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "branch",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "CMRS details",
            {
                "fields": ("role", "branch", "phone"),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "CMRS details",
            {
                "fields": ("role", "branch", "phone"),
            },
        ),
    )