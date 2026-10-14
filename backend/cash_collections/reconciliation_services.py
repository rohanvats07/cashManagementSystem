
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    BankDeposit,
    BankDepositItem,
    BankReconciliation,
    CashSubmission,
)


ZERO = Decimal("0.00")


def is_admin(user):
    return user.is_superuser or user.role == user.Role.ADMIN


def validate_branch_access(user, branch_id):
    if is_admin(user):
        return

    if (
        user.role != user.Role.BRANCH_MANAGER
        or user.branch_id != branch_id
    ):
        raise ValidationError(
            "You can manage deposits only for your own branch."
        )


@transaction.atomic
def create_bank_deposit(*, submission_ids, created_by):
    if not (
        is_admin(created_by)
        or created_by.role == created_by.Role.BRANCH_MANAGER
    ):
        raise ValidationError(
            "Only administrators or branch managers can create deposits."
        )

    if not submission_ids:
        raise ValidationError({
            "submission_ids": "Select at least one cash submission."
        })

    if len(submission_ids) != len(set(submission_ids)):
        raise ValidationError({
            "submission_ids": "Duplicate submission IDs are not allowed."
        })

    submissions = list(
        CashSubmission.objects.select_for_update()
        .filter(id__in=submission_ids)
        .order_by("id")
    )

    if len(submissions) != len(submission_ids):
        raise ValidationError(
            "One or more cash submissions were not found."
        )

    if any(
        item.status != CashSubmission.Status.ACCEPTED
        for item in submissions
    ):
        raise ValidationError(
            "Only accepted cash submissions can be deposited."
        )

    branch_ids = {item.branch_id for item in submissions}

    if len(branch_ids) != 1:
        raise ValidationError(
            "All submissions in a deposit must belong to the same branch."
        )

    branch_id = next(iter(branch_ids))
    validate_branch_access(created_by, branch_id)

    if BankDepositItem.objects.filter(
        submission_id__in=submission_ids
    ).exists():
        raise ValidationError(
            "One or more submissions are already part of a bank deposit."
        )

    expected_amount = sum(
        (item.amount for item in submissions),
        ZERO,
    )

    deposit = BankDeposit.objects.create(
        branch_id=branch_id,
        created_by=created_by,
        expected_amount=expected_amount,
    )

    BankDepositItem.objects.bulk_create([
        BankDepositItem(deposit=deposit, submission=item)
        for item in submissions
    ])

    return deposit


@transaction.atomic
def mark_bank_deposit_complete(
    *,
    deposit_id,
    updated_by,
    bank_name,
    bank_reference,
    deposited_amount,
    deposit_date=None,
):
    deposit = (
        BankDeposit.objects.select_for_update()
        .filter(pk=deposit_id)
        .first()
    )

    if deposit is None:
        raise ValidationError({"deposit": "Deposit not found."})

    validate_branch_access(updated_by, deposit.branch_id)

    if deposit.status != BankDeposit.Status.PREPARED:
        raise ValidationError(
            "Only prepared deposits can be marked as deposited."
        )

    bank_name = bank_name.strip()
    bank_reference = bank_reference.strip()
    deposited_amount = Decimal(str(deposited_amount)).quantize(
        Decimal("0.01")
    )
    deposit_date = deposit_date or timezone.localdate()

    if not bank_name:
        raise ValidationError({"bank_name": "Bank name is required."})

    if not bank_reference:
        raise ValidationError({
            "bank_reference": "Bank reference is required."
        })

    if deposited_amount <= ZERO:
        raise ValidationError({
            "deposited_amount": "Deposited amount must be positive."
        })

    if deposit_date > timezone.localdate():
        raise ValidationError({
            "deposit_date": "Deposit date cannot be in the future."
        })

    if BankDeposit.objects.filter(
        bank_reference=bank_reference
    ).exclude(pk=deposit.pk).exists():
        raise ValidationError({
            "bank_reference": "This bank reference is already in use."
        })

    deposit.bank_name = bank_name
    deposit.bank_reference = bank_reference
    deposit.deposited_amount = deposited_amount
    deposit.deposit_date = deposit_date
    deposit.status = BankDeposit.Status.DEPOSITED
    deposit.save(
        update_fields=[
            "bank_name",
            "bank_reference",
            "deposited_amount",
            "deposit_date",
            "status",
            "updated_at",
        ]
    )

    return deposit


@transaction.atomic
def reconcile_company_account(
    *,
    deposit_id,
    reconciled_by,
    statement_reference,
    statement_date,
    credited_amount,
    notes="",
):
    if not is_admin(reconciled_by):
        raise ValidationError(
            "Only an administrator can reconcile company-account credits."
        )

    deposit = (
        BankDeposit.objects.select_for_update()
        .filter(pk=deposit_id)
        .first()
    )

    if deposit is None:
        raise ValidationError({"deposit": "Deposit not found."})

    if deposit.status != BankDeposit.Status.DEPOSITED:
        raise ValidationError(
            "Only deposited records can be reconciled."
        )

    if BankReconciliation.objects.filter(deposit=deposit).exists():
        raise ValidationError(
            "This deposit has already been reconciled."
        )

    statement_reference = statement_reference.strip()
    credited_amount = Decimal(str(credited_amount)).quantize(
        Decimal("0.01")
    )

    if not statement_reference:
        raise ValidationError({
            "statement_reference": "Statement reference is required."
        })

    if credited_amount < ZERO:
        raise ValidationError({
            "credited_amount": "Credited amount cannot be negative."
        })

    if statement_date > timezone.localdate():
        raise ValidationError({
            "statement_date": "Statement date cannot be in the future."
        })

    if BankReconciliation.objects.filter(
        statement_reference=statement_reference
    ).exists():
        raise ValidationError({
            "statement_reference": "This statement reference is already in use."
        })

    expected = deposit.expected_amount
    deposited = deposit.deposited_amount

    if credited_amount == expected and deposited == expected:
        result = BankReconciliation.Status.MATCHED
        deposit_status = BankDeposit.Status.RECONCILED
    elif credited_amount < expected:
        result = BankReconciliation.Status.SHORT
        deposit_status = BankDeposit.Status.DISCREPANCY
    elif credited_amount > expected:
        result = BankReconciliation.Status.EXCESS
        deposit_status = BankDeposit.Status.DISCREPANCY
    else:
        result = BankReconciliation.Status.DISCREPANCY
        deposit_status = BankDeposit.Status.DISCREPANCY

    reconciliation = BankReconciliation.objects.create(
        deposit=deposit,
        statement_reference=statement_reference,
        statement_date=statement_date,
        credited_amount=credited_amount,
        status=result,
        notes=notes,
        reconciled_by=reconciled_by,
    )

    deposit.status = deposit_status
    deposit.save(update_fields=["status", "updated_at"])

    return reconciliation
