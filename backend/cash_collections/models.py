
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_receipt_number():
    return f"RCPT-{uuid.uuid4().hex[:16].upper()}"


def generate_submission_number():
    return f"CSUB-{uuid.uuid4().hex[:16].upper()}"

def generate_deposit_number():
    return f"DEP-{uuid.uuid4().hex[:16].upper()}"

class CashCollection(models.Model):
    receipt_number = models.CharField(
        max_length=30,
        unique=True,
        default=generate_receipt_number,
        editable=False,
    )
    idempotency_key = models.CharField(max_length=100, unique=True)

    loan = models.ForeignKey(
        "loans.Loan",
        on_delete=models.PROTECT,
        related_name="cash_collections",
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="cash_collections",
    )
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_collections",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    collection_date = models.DateField(default=timezone.localdate)
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["collected_by", "collection_date"]),
            models.Index(fields=["loan", "collection_date"]),
        ]

    def __str__(self):
        return f"{self.receipt_number} - {self.amount}"


class CollectionAllocation(models.Model):
    collection = models.ForeignKey(
        CashCollection,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    schedule = models.ForeignKey(
        "loans.RepaymentSchedule",
        on_delete=models.PROTECT,
        related_name="collection_allocations",
    )
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "schedule"],
                name="unique_collection_schedule_allocation",
            ),
            models.CheckConstraint(
                condition=models.Q(principal_amount__gte=0),
                name="allocation_principal_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(interest_amount__gte=0),
                name="allocation_interest_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.collection.receipt_number} - {self.schedule}"


class CashSubmission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    submission_number = models.CharField(
        max_length=30,
        unique=True,
        default=generate_submission_number,
        editable=False,
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="cash_submissions",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_submissions",
    )
    submission_date = models.DateField(default=timezone.localdate)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_cash_submissions",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["branch", "status"]),
            models.Index(fields=["submitted_by", "submission_date"]),
        ]

    def __str__(self):
        return f"{self.submission_number} - {self.amount}"


class CashSubmissionItem(models.Model):
    submission = models.ForeignKey(
        CashSubmission,
        on_delete=models.PROTECT,
        related_name="items",
    )
    collection = models.OneToOneField(
        CashCollection,
        on_delete=models.PROTECT,
        related_name="submission_item",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.submission.submission_number} - {self.collection.receipt_number}"


class BankDeposit(models.Model):
    class Status(models.TextChoices):
        PREPARED = "PREPARED", "Prepared"
        DEPOSITED = "DEPOSITED", "Deposited"
        RECONCILED = "RECONCILED", "Reconciled"
        DISCREPANCY = "DISCREPANCY", "Discrepancy"

    deposit_number = models.CharField(
        max_length=30,
        unique=True,
        default=generate_deposit_number,
        editable=False,
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="bank_deposits",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_bank_deposits",
    )
    deposit_date = models.DateField(default=timezone.localdate)
    bank_name = models.CharField(max_length=150, blank=True)
    bank_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )
    expected_amount = models.DecimalField(max_digits=14, decimal_places=2)
    deposited_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PREPARED,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["branch", "status"]),
            models.Index(fields=["deposit_date", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expected_amount__gt=0),
                name="bank_deposit_expected_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(deposited_amount__isnull=True)
                    | models.Q(deposited_amount__gt=0)
                ),
                name="bank_deposit_actual_positive",
            ),
        ]

    def __str__(self):
        return f"{self.deposit_number} - {self.expected_amount}"


class BankDepositItem(models.Model):
    deposit = models.ForeignKey(
        BankDeposit,
        on_delete=models.PROTECT,
        related_name="items",
    )
    submission = models.OneToOneField(
        CashSubmission,
        on_delete=models.PROTECT,
        related_name="bank_deposit_item",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.deposit.deposit_number} - {self.submission.submission_number}"


class BankReconciliation(models.Model):
    class Status(models.TextChoices):
        MATCHED = "MATCHED", "Matched"
        SHORT = "SHORT", "Short Credit"
        EXCESS = "EXCESS", "Excess Credit"
        DISCREPANCY = "DISCREPANCY", "Other Discrepancy"

    deposit = models.OneToOneField(
        BankDeposit,
        on_delete=models.PROTECT,
        related_name="reconciliation",
    )
    statement_reference = models.CharField(max_length=100, unique=True)
    statement_date = models.DateField()
    credited_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        db_index=True,
    )
    notes = models.CharField(max_length=500, blank=True)
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bank_reconciliations",
    )
    reconciled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reconciled_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(credited_amount__gte=0),
                name="bank_credit_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.deposit.deposit_number} - {self.status}"
