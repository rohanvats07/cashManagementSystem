from django.contrib import admin

from loans.models import Loan, RepaymentSchedule


class RepaymentScheduleInline(admin.TabularInline):
    model = RepaymentSchedule
    extra = 0
    can_delete = False
    readonly_fields = (
        "installment_number",
        "due_date",
        "principal_due",
        "interest_due",
        "total_due",
        "principal_paid",
        "interest_paid",
        "status",
    )


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "loan_number",
        "customer",
        "principal_amount",
        "annual_interest_rate",
        "tenor_months",
        "emi_amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "disbursement_date")
    search_fields = ("loan_number", "customer__full_name", "customer__phone")
    readonly_fields = (
        "loan_number",
        "emi_amount",
        "total_interest_amount",
        "total_payable",
        "created_by",
        "created_at",
        "updated_at",
    )
    inlines = [RepaymentScheduleInline]


@admin.register(RepaymentSchedule)
class RepaymentScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "loan",
        "installment_number",
        "due_date",
        "principal_due",
        "interest_due",
        "total_due",
        "status",
    )
    list_filter = ("status", "due_date")
    search_fields = ("loan__loan_number", "loan__customer__full_name")
    readonly_fields = (
        "loan",
        "installment_number",
        "due_date",
        "principal_due",
        "interest_due",
        "total_due",
        "principal_paid",
        "interest_paid",
        "status",
        "created_at",
        "updated_at",
    )