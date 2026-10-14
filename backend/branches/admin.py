from django.contrib import admin

from branches.models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "city",
        "state",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "state", "city")
    search_fields = ("code", "name", "city", "state")
    readonly_fields = ("created_at", "updated_at")