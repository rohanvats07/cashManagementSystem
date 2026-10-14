import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext

from django.db import transaction
from rest_framework.exceptions import ValidationError

from loans.models import Loan, RepaymentSchedule


MONEY_PLACES = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value):
    return Decimal(value).quantize(
        MONEY_PLACES,
        rounding=ROUND_HALF_UP,
    )


def add_months(source_date, months):
    """
    Add calendar months while preserving month-end behavior.

    Example: January 31 + one month = February 28 or 29.
    """
    month_index = source_date.month - 1 + months
    year = source_date.year + month_index // 12
    month = month_index % 12 + 1

    last_day = calendar.monthrange(year, month)[1]
    day = min(source_date.day, last_day)

    return date(year, month, day)


def calculate_emi(principal, annual_interest_rate, tenor_months):
    principal = Decimal(principal)
    annual_interest_rate = Decimal(annual_interest_rate)

    if principal <= 0:
        raise ValidationError(
            {"principal_amount": "Principal must be greater than zero."}
        )

    if annual_interest_rate < 0:
        raise ValidationError(
            {"annual_interest_rate": "Interest rate cannot be negative."}
        )

    if tenor_months < 1:
        raise ValidationError(
            {"tenor_months": "Tenor must be at least one month."}
        )

    with localcontext() as context:
        context.prec = 28

        monthly_rate = annual_interest_rate / Decimal("1200")

        if monthly_rate == 0:
            return money(principal / Decimal(tenor_months))

        factor = (Decimal("1") + monthly_rate) ** tenor_months

        emi = (
            principal
            * monthly_rate
            * factor
            / (factor - Decimal("1"))
        )

        return money(emi)


@transaction.atomic
def create_loan_with_schedule(validated_data, created_by):
    """
    Create a loan and all its installments atomically.

    If any installment cannot be created, the entire operation rolls back.
    """
    data = validated_data.copy()

    principal = Decimal(data["principal_amount"])
    annual_rate = Decimal(data["annual_interest_rate"])
    tenor = data["tenor_months"]
    disbursement_date = data["disbursement_date"]

    first_due_date = data.get("first_due_date")

    if first_due_date is None:
        first_due_date = add_months(disbursement_date, 1)

    emi = calculate_emi(principal, annual_rate, tenor)
    data["first_due_date"] = first_due_date

    loan = Loan.objects.create(
        **data,
        emi_amount=emi,
        created_by=created_by,
    )

    outstanding_principal = principal
    total_interest = ZERO
    schedule_rows = []

    with localcontext() as context:
        context.prec = 28

        monthly_rate = annual_rate / Decimal("1200")

        for installment_number in range(1, tenor + 1):
            interest_due = money(outstanding_principal * monthly_rate)

            if installment_number == tenor:
                # Adjust the final installment for accumulated rounding.
                principal_due = outstanding_principal
            else:
                principal_due = money(emi - interest_due)

                # Protect against an invalid schedule if terms are changed.
                principal_due = min(principal_due, outstanding_principal)

            principal_due = money(principal_due)
            total_due = money(principal_due + interest_due)

            schedule_rows.append(
                RepaymentSchedule(
                    loan=loan,
                    installment_number=installment_number,
                    due_date=add_months(first_due_date, installment_number - 1),
                    principal_due=principal_due,
                    interest_due=interest_due,
                    total_due=total_due,
                )
            )

            outstanding_principal = money(
                outstanding_principal - principal_due
            )
            total_interest += interest_due

    if outstanding_principal != ZERO:
        raise ValidationError(
            "The repayment schedule did not amortize the loan completely."
        )

    RepaymentSchedule.objects.bulk_create(schedule_rows)

    loan.total_interest_amount = money(total_interest)
    loan.total_payable = money(principal + total_interest)
    loan.save(
        update_fields=[
            "total_interest_amount",
            "total_payable",
            "updated_at",
        ]
    )

    return loan