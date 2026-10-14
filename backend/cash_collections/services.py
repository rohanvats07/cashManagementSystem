
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from loans.models import Loan, RepaymentSchedule
from .models import (
    CashCollection,
    CollectionAllocation,
    CashSubmission,
    CashSubmissionItem,
)


ZERO = Decimal("0.00")


def record_cash_collection(
    *,
    loan_id,
    amount,
    collected_by,
    idempotency_key,
    collection_date=None,
    notes="",
):
    amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    collection_date = collection_date or timezone.localdate()

    if amount <= ZERO:
        raise ValidationError({"amount": "Amount must be greater than zero."})

    if collection_date > timezone.localdate():
        raise ValidationError({
            "collection_date": "Collection date cannot be in the future."
        })

    try:
        return _record_cash_collection(
            loan_id=loan_id,
            amount=amount,
            collected_by=collected_by,
            idempotency_key=idempotency_key,
            collection_date=collection_date,
            notes=notes,
        )
    except IntegrityError:
        # Another request may have used the same key concurrently.
        existing = CashCollection.objects.filter(
            idempotency_key=idempotency_key
        ).first()

        if existing is None:
            raise

        if (
            existing.loan_id != int(loan_id)
            or existing.amount != amount
            or existing.collected_by_id != collected_by.id
        ):
            raise ValidationError({
                "idempotency_key": "This key was already used for a different collection."
            })

        return existing


@transaction.atomic
def _record_cash_collection(
    *,
    loan_id,
    amount,
    collected_by,
    idempotency_key,
    collection_date,
    notes,
):
    existing = CashCollection.objects.filter(
        idempotency_key=idempotency_key
    ).first()

    if existing:
        if (
            existing.loan_id != int(loan_id)
            or existing.amount != amount
            or existing.collected_by_id != collected_by.id
        ):
            raise ValidationError({
                "idempotency_key": "This key was already used for a different collection."
            })
        return existing

    if collected_by.role != collected_by.Role.COLLECTION_AGENT:
        raise ValidationError(
            "Only collection agents can record customer cash collections."
        )

    loan = (
        Loan.objects.select_for_update()
        .select_related("customer", "customer__branch", "customer__assigned_agent")
        .filter(pk=loan_id)
        .first()
    )

    if loan is None:
        raise ValidationError({"loan": "Loan not found."})

    if loan.status != Loan.Status.ACTIVE:
        raise ValidationError({"loan": "Only active loans can receive payments."})

    customer = loan.customer

    if not customer.is_active:
        raise ValidationError({"loan": "The customer is inactive."})

    if not customer.branch.is_active:
        raise ValidationError({"loan": "The customer's branch is inactive."})

    if (
        customer.assigned_agent_id != collected_by.id
        or customer.branch_id != collected_by.branch_id
    ):
        raise ValidationError(
            "You can collect payments only from customers assigned to you "
            "within your branch."
        )

    schedules = list(
        RepaymentSchedule.objects.select_for_update()
        .filter(loan=loan)
        .order_by("installment_number")
    )

    if not schedules:
        raise ValidationError({"loan": "This loan has no repayment schedule."})

    outstanding = sum(
        (
            schedule.total_due
            - schedule.principal_paid
            - schedule.interest_paid
        )
        for schedule in schedules
    )

    if outstanding <= ZERO:
        raise ValidationError({"loan": "This loan has no outstanding balance."})

    if amount > outstanding:
        raise ValidationError({
            "amount": f"Amount cannot exceed the outstanding balance of {outstanding:.2f}."
        })

    collection = CashCollection.objects.create(
        loan=loan,
        customer=customer,
        collected_by=collected_by,
        amount=amount,
        idempotency_key=idempotency_key,
        collection_date=collection_date,
        notes=notes,
    )

    remaining = amount

    for schedule in schedules:
        if remaining <= ZERO:
            break

        interest_outstanding = schedule.interest_due - schedule.interest_paid
        principal_outstanding = schedule.principal_due - schedule.principal_paid

        interest_payment = min(remaining, interest_outstanding)
        remaining -= interest_payment

        principal_payment = min(remaining, principal_outstanding)
        remaining -= principal_payment

        if interest_payment == ZERO and principal_payment == ZERO:
            continue

        schedule.interest_paid += interest_payment
        schedule.principal_paid += principal_payment

        if (
            schedule.interest_paid == schedule.interest_due
            and schedule.principal_paid == schedule.principal_due
        ):
            schedule.status = RepaymentSchedule.Status.PAID
        elif schedule.due_date < timezone.localdate():
            schedule.status = RepaymentSchedule.Status.OVERDUE
        else:
            schedule.status = RepaymentSchedule.Status.PARTIAL

        schedule.save(
            update_fields=[
                "interest_paid",
                "principal_paid",
                "status",
                "updated_at",
            ]
        )

        CollectionAllocation.objects.create(
            collection=collection,
            schedule=schedule,
            interest_amount=interest_payment,
            principal_amount=principal_payment,
        )

    if remaining != ZERO:
        # This should never occur if outstanding calculations are correct.
        raise ValidationError("Payment allocation could not be completed.")

    if all(
        schedule.principal_paid == schedule.principal_due
        and schedule.interest_paid == schedule.interest_due
        for schedule in schedules
    ):
        loan.status = Loan.Status.CLOSED
        loan.save(update_fields=["status", "updated_at"])

    return collection


@transaction.atomic
def submit_collected_cash(*, collection_ids, submitted_by):
    if submitted_by.role != submitted_by.Role.COLLECTION_AGENT:
        raise ValidationError(
            "Only collection agents can submit collected cash."
        )

    if not collection_ids:
        raise ValidationError({
            "collection_ids": "Select at least one collection."
        })

    if len(collection_ids) != len(set(collection_ids)):
        raise ValidationError({
            "collection_ids": "Duplicate collection IDs are not allowed."
        })

    collections = list(
        CashCollection.objects.select_for_update()
        .filter(id__in=collection_ids, collected_by=submitted_by)
        .select_related("customer__branch")
        .order_by("id")
    )

    if len(collections) != len(collection_ids):
        raise ValidationError(
            "One or more collections do not exist or do not belong to you."
        )

    branch_ids = {collection.customer.branch_id for collection in collections}

    if len(branch_ids) != 1 or submitted_by.branch_id not in branch_ids:
        raise ValidationError(
            "All submitted collections must belong to your own branch."
        )

    already_submitted = CashSubmissionItem.objects.filter(
        collection_id__in=collection_ids
    ).exists()

    if already_submitted:
        raise ValidationError(
            "One or more collections have already been submitted."
        )

    total_amount = sum((collection.amount for collection in collections), ZERO)

    submission = CashSubmission.objects.create(
        branch_id=next(iter(branch_ids)),
        submitted_by=submitted_by,
        amount=total_amount,
    )

    CashSubmissionItem.objects.bulk_create([
        CashSubmissionItem(submission=submission, collection=collection)
        for collection in collections
    ])

    return submission


@transaction.atomic
def review_cash_submission(
    *,
    submission_id,
    reviewed_by,
    decision,
    review_notes="",
):
    submission = (
        CashSubmission.objects.select_for_update()
        .select_related("branch")
        .filter(pk=submission_id)
        .first()
    )

    if submission is None:
        raise ValidationError({"submission": "Submission not found."})

    if reviewed_by.role not in (
        reviewed_by.Role.ADMIN,
        reviewed_by.Role.BRANCH_MANAGER,
    ) and not reviewed_by.is_superuser:
        raise ValidationError(
            "Only administrators or branch managers can review submissions."
        )

    if (
        not reviewed_by.is_superuser
        and reviewed_by.role != reviewed_by.Role.ADMIN
        and reviewed_by.branch_id != submission.branch_id
    ):
        raise ValidationError(
            "You can review submissions only for your own branch."
        )

    if submission.status != CashSubmission.Status.SUBMITTED:
        raise ValidationError(
            "This submission has already been reviewed."
        )

    if decision not in (
        CashSubmission.Status.ACCEPTED,
        CashSubmission.Status.REJECTED,
    ):
        raise ValidationError({
            "decision": "Decision must be ACCEPTED or REJECTED."
        })

    submission.status = decision
    submission.reviewed_by = reviewed_by
    submission.reviewed_at = timezone.now()
    submission.review_notes = review_notes
    submission.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
        ]
    )

    return submission
