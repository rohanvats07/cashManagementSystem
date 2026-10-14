from django.contrib import admin

from customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "customer_code",
        "full_name",
        "phone",
        "branch",
        "assigned_agent",
        "is_active",
    )
    list_filter = ("branch", "is_active")
    search_fields = ("customer_code", "full_name", "phone", "email")
    readonly_fields = ("customer_code", "created_at", "updated_at")