
from rest_framework import serializers

from .models import BankDeposit, BankDepositItem, BankReconciliation


class BankDepositItemSerializer(serializers.ModelSerializer):
    submission_number = serializers.CharField(
        source="submission.submission_number",
        read_only=True,
    )
    submission_amount = serializers.DecimalField(
        source="submission.amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = BankDepositItem
        fields = [
            "id",
            "submission",
            "submission_number",
            "submission_amount",
        ]


class BankReconciliationSerializer(serializers.ModelSerializer):
    reconciled_by_username = serializers.CharField(
        source="reconciled_by.username",
        read_only=True,
    )

    class Meta:
        model = BankReconciliation
        fields = [
            "id",
            "statement_reference",
            "statement_date",
            "credited_amount",
            "status",
            "notes",
            "reconciled_by",
            "reconciled_by_username",
            "reconciled_at",
        ]
        read_only_fields = fields


class BankDepositSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True,
    )
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )
    items = BankDepositItemSerializer(many=True, read_only=True)
    reconciliation = BankReconciliationSerializer(read_only=True)

    class Meta:
        model = BankDeposit
        fields = [
            "id",
            "deposit_number",
            "branch",
            "branch_name",
            "created_by",
            "created_by_username",
            "deposit_date",
            "bank_name",
            "bank_reference",
            "expected_amount",
            "deposited_amount",
            "status",
            "items",
            "reconciliation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class BankDepositCreateSerializer(serializers.Serializer):
    submission_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )

    def validate_submission_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Duplicate submission IDs are not allowed."
            )
        return value


class MarkBankDepositSerializer(serializers.Serializer):
    bank_name = serializers.CharField(max_length=150)
    bank_reference = serializers.CharField(max_length=100)
    deposited_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    deposit_date = serializers.DateField(required=False)

    def validate_deposited_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Deposited amount must be greater than zero."
            )
        return value


class ReconcileCompanyAccountSerializer(serializers.Serializer):
    statement_reference = serializers.CharField(max_length=100)
    statement_date = serializers.DateField()
    credited_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_credited_amount(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Credited amount cannot be negative."
            )
        return value
