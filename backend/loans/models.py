import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


def generate_loan_number():
    return f"LN-{uuid.uuid4().hex[:12].upper()}"


class Loan(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CLOSED = "CLOSED", "Closed"
        DEFAULTED = "DEFAULTED", "Defaulted"
        CANCELLED = "CANCELLED", "Cancelled"

    loan_number = models.CharField(
        max_length=16,
        unique=True,
        default=generate_loan_number,
        editable=False,
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="loans",
    )

    principal_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    annual_interest_rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Annual nominal interest rate in percent.",
    )
    tenor_months = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )

    disbursement_date = models.DateField()
    first_due_date = models.DateField()

    emi_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    total_interest_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    total_payable = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_loans",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["disbursement_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(principal_amount__gt=0),
                name="loan_principal_positive",
            ),
            models.CheckConstraint(
                condition=Q(annual_interest_rate__gte=0),
                name="loan_interest_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(tenor_months__gte=1),
                name="loan_tenor_positive",
            ),
        ]

    def __str__(self):
        return f"{self.loan_number} - {self.customer.full_name}"


class RepaymentSchedule(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PARTIAL = "PARTIAL", "Partially Paid"
        PAID = "PAID", "Paid"
        OVERDUE = "OVERDUE", "Overdue"

    loan = models.ForeignKey(
        Loan,
        on_delete=models.PROTECT,
        related_name="repayment_schedules",
    )
    installment_number = models.PositiveSmallIntegerField()
    due_date = models.DateField()

    principal_due = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    interest_due = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    total_due = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    principal_paid = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    interest_paid = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["installment_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["loan", "installment_number"],
                name="unique_loan_installment",
            ),
            models.CheckConstraint(
                condition=Q(installment_number__gte=1),
                name="installment_number_positive",
            ),
            models.CheckConstraint(
                condition=Q(principal_due__gte=0),
                name="schedule_principal_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(interest_due__gte=0),
                name="schedule_interest_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(total_due__gte=0),
                name="schedule_total_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(principal_paid__gte=0),
                name="schedule_principal_paid_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(interest_paid__gte=0),
                name="schedule_interest_paid_nonnegative",
            ),
        ]

    @property
    def amount_paid(self):
        return self.principal_paid + self.interest_paid

    @property
    def outstanding_amount(self):
        return self.total_due - self.amount_paid

    def __str__(self):
        return f"{self.loan.loan_number} - Installment {self.installment_number}"