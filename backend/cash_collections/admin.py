
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


from django.contrib import admin

from .models import BankDeposit, BankDepositItem, BankReconciliation


class BankDepositItemInline(admin.TabularInline):
    model = BankDepositItem
    extra = 0
    can_delete = False
    readonly_fields = ["submission"]


@admin.register(BankDeposit)
class BankDepositAdmin(admin.ModelAdmin):
    list_display = [
        "deposit_number",
        "branch",
        "bank_name",
        "expected_amount",
        "deposited_amount",
        "status",
        "deposit_date",
    ]
    list_filter = ["status", "branch", "deposit_date"]
    search_fields = ["deposit_number", "bank_reference", "branch__name"]
    readonly_fields = [
        "deposit_number",
        "branch",
        "created_by",
        "deposit_date",
        "bank_name",
        "bank_reference",
        "expected_amount",
        "deposited_amount",
        "status",
        "created_at",
        "updated_at",
    ]
    inlines = [BankDepositItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = [
        "deposit",
        "statement_reference",
        "credited_amount",
        "status",
        "reconciled_by",
        "reconciled_at",
    ]
    list_filter = ["status", "statement_date"]
    search_fields = [
        "statement_reference",
        "deposit__deposit_number",
    ]
    readonly_fields = [
        "deposit",
        "statement_reference",
        "statement_date",
        "credited_amount",
        "status",
        "notes",
        "reconciled_by",
        "reconciled_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
