from rest_framework import serializers

from accounts.models import User
from branches.models import Branch
from customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True,
    )
    assigned_agent_username = serializers.CharField(
        source="assigned_agent.username",
        read_only=True,
        default=None,
    )

    class Meta:
        model = Customer
        fields = [
            "id",
            "customer_code",
            "full_name",
            "phone",
            "email",
            "address",
            "branch",
            "branch_name",
            "assigned_agent",
            "assigned_agent_username",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_code",
            "branch_name",
            "assigned_agent_username",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        branch = attrs.get(
            "branch",
            self.instance.branch if self.instance else None,
        )
        agent = attrs.get(
            "assigned_agent",
            self.instance.assigned_agent if self.instance else None,
        )

        if branch is None:
            raise serializers.ValidationError(
                {"branch": "A branch is required."}
            )

        if not branch.is_active:
            raise serializers.ValidationError(
                {"branch": "Customers cannot be assigned to an inactive branch."}
            )

        if agent is not None:
            if agent.role != User.Role.COLLECTION_AGENT:
                raise serializers.ValidationError(
                    {
                        "assigned_agent":
                            "The assigned user must be a collection agent."
                    }
                )

            if not agent.is_active:
                raise serializers.ValidationError(
                    {"assigned_agent": "The assigned agent is inactive."}
                )

            if agent.branch_id != branch.id:
                raise serializers.ValidationError(
                    {
                        "assigned_agent":
                            "The agent and customer must belong to the same branch."
                    }
                )

        if (
            not user.is_superuser
            and user.role == User.Role.BRANCH_MANAGER
            and branch.id != user.branch_id
        ):
            raise serializers.ValidationError(
                {"branch": "You can manage customers only in your own branch."}
            )

        return attrs