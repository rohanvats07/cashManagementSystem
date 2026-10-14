
from django.contrib import admin

from .models import (
    CashCollection,
    CollectionAllocation,
    CashSubmission,
    CashSubmissionItem,
)


class CollectionAllocationInline(admin.TabularInline):
    model = CollectionAllocation
    extra = 0
    can_delete = False
    readonly_fields = [
        "schedule",
        "principal_amount",
        "interest_amount",
    ]


@admin.register(CashCollection)
class CashCollectionAdmin(admin.ModelAdmin):
    list_display = [
        "receipt_number",
        "loan",
        "customer",
        "collected_by",
        "amount",
        "collection_date",
        "created_at",
    ]
    search_fields = [
        "receipt_number",
        "customer__full_name",
        "loan__loan_number",
        "collected_by__username",
    ]
    list_filter = ["collection_date"]
    readonly_fields = [
        "receipt_number",
        "idempotency_key",
        "loan",
        "customer",
        "collected_by",
        "amount",
        "collection_date",
        "notes",
        "created_at",
    ]
    inlines = [CollectionAllocationInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CashSubmissionItemInline(admin.TabularInline):
    model = CashSubmissionItem
    extra = 0
    can_delete = False
    readonly_fields = ["collection"]


@admin.register(CashSubmission)
class CashSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "submission_number",
        "branch",
        "submitted_by",
        "amount",
        "status",
        "submission_date",
    ]
    list_filter = ["status", "submission_date", "branch"]
    readonly_fields = [
        "submission_number",
        "branch",
        "submitted_by",
        "submission_date",
        "amount",
        "status",
        "reviewed_by",
        "reviewed_at",
        "review_notes",
        "created_at",
    ]
    inlines = [CashSubmissionItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
