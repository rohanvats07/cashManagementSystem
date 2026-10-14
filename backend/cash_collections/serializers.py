
from rest_framework import serializers

from .models import (
    CashCollection,
    CollectionAllocation,
    CashSubmission,
    CashSubmissionItem,
)
from loans.models import Loan

class CollectionAllocationSerializer(serializers.ModelSerializer):
    installment_number = serializers.IntegerField(
        source="schedule.installment_number",
        read_only=True,
    )

    class Meta:
        model = CollectionAllocation
        fields = [
            "id",
            "installment_number",
            "principal_amount",
            "interest_amount",
        ]


class CashCollectionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.full_name",
        read_only=True,
    )
    loan_number = serializers.CharField(
        source="loan.loan_number",
        read_only=True,
    )
    agent_username = serializers.CharField(
        source="collected_by.username",
        read_only=True,
    )
    allocations = CollectionAllocationSerializer(many=True, read_only=True)

    class Meta:
        model = CashCollection
        fields = [
            "id",
            "receipt_number",
            "idempotency_key",
            "loan",
            "loan_number",
            "customer",
            "customer_name",
            "collected_by",
            "agent_username",
            "amount",
            "collection_date",
            "notes",
            "allocations",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "receipt_number",
            "customer",
            "collected_by",
            "created_at",
        ]


class CashCollectionCreateSerializer(serializers.Serializer):
    loan = serializers.PrimaryKeyRelatedField(queryset=Loan.objects.all())
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    idempotency_key = serializers.CharField(max_length=100)
    collection_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )
        return value

    def validate_idempotency_key(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "An idempotency key is required."
            )
        return value


class CashSubmissionItemSerializer(serializers.ModelSerializer):
    receipt_number = serializers.CharField(
        source="collection.receipt_number",
        read_only=True,
    )
    collection_amount = serializers.DecimalField(
        source="collection.amount",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = CashSubmissionItem
        fields = [
            "id",
            "collection",
            "receipt_number",
            "collection_amount",
        ]


class CashSubmissionSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True,
    )
    agent_username = serializers.CharField(
        source="submitted_by.username",
        read_only=True,
    )
    items = CashSubmissionItemSerializer(many=True, read_only=True)

    class Meta:
        model = CashSubmission
        fields = [
            "id",
            "submission_number",
            "branch",
            "branch_name",
            "submitted_by",
            "agent_username",
            "submission_date",
            "amount",
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "items",
            "created_at",
        ]
        read_only_fields = fields


class CashSubmissionCreateSerializer(serializers.Serializer):
    collection_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )

    def validate_collection_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Duplicate collection IDs are not allowed."
            )
        return value


class CashSubmissionReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(
        choices=[
            CashSubmission.Status.ACCEPTED,
            CashSubmission.Status.REJECTED,
        ]
    )
    review_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
    )
