from rest_framework import serializers

from accounts.models import User
from customers.models import Customer
from loans.models import Loan, RepaymentSchedule
from loans.services import create_loan_with_schedule


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    amount_paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    outstanding_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = RepaymentSchedule
        fields = [
            "id",
            "loan",
            "installment_number",
            "due_date",
            "principal_due",
            "interest_due",
            "total_due",
            "principal_paid",
            "interest_paid",
            "amount_paid",
            "outstanding_amount",
            "status",
        ]
        read_only_fields = fields


class LoanSerializer(serializers.ModelSerializer):
    customer_code = serializers.CharField(
        source="customer.customer_code",
        read_only=True,
    )
    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True,
    )
    branch_id = serializers.IntegerField(
        source="customer.branch_id",
        read_only=True,
    )
    schedule_count = serializers.IntegerField(read_only=True)
    first_due_date = serializers.DateField(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Loan
        fields = [
            "id",
            "loan_number",
            "customer",
            "customer_code",
            "customer_name",
            "branch_id",
            "principal_amount",
            "annual_interest_rate",
            "tenor_months",
            "disbursement_date",
            "first_due_date",
            "emi_amount",
            "total_interest_amount",
            "total_payable",
            "status",
            "schedule_count",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "loan_number",
            "emi_amount",
            "total_interest_amount",
            "total_payable",
            "status",
            "schedule_count",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate_tenor_months(self, value):
        if not 1 <= value <= 360:
            raise serializers.ValidationError(
                "Loan tenor must be between 1 and 360 months."
            )

        return value

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        customer = attrs.get(
            "customer",
            self.instance.customer if self.instance else None,
        )

        if customer is None:
            raise serializers.ValidationError(
                {"customer": "A customer is required."}
            )

        if not customer.is_active:
            raise serializers.ValidationError(
                {"customer": "Cannot create a loan for an inactive customer."}
            )

        if not customer.branch.is_active:
            raise serializers.ValidationError(
                {"customer": "The customer's branch is inactive."}
            )

        if (
            not user.is_superuser
            and user.role == User.Role.BRANCH_MANAGER
            and customer.branch_id != user.branch_id
        ):
            raise serializers.ValidationError(
                {"customer": "You can create loans only for customers in your branch."}
            )

        disbursement_date = attrs.get("disbursement_date")
        first_due_date = attrs.get("first_due_date")

        if (
            disbursement_date is not None
            and first_due_date is not None
            and first_due_date <= disbursement_date
        ):
            raise serializers.ValidationError(
                {
                    "first_due_date":
                        "The first due date must be after the disbursement date."
                }
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]

        return create_loan_with_schedule(
            validated_data=validated_data,
            created_by=request.user,
        )