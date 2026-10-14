from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import User
from branches.models import Branch


class UserProfileSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True,
        default=None,
    )
    branch_code = serializers.CharField(
        source="branch.code",
        read_only=True,
        default=None,
    )
    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "role_display",
            "branch",
            "branch_name",
            "branch_code",
            "is_active",
        ]
        read_only_fields = fields


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "branch",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        role = attrs.get("role", User.Role.COLLECTION_AGENT)
        branch = attrs.get("branch")

        if role in {
            User.Role.COLLECTION_AGENT,
            User.Role.BRANCH_MANAGER,
        } and branch is None:
            raise serializers.ValidationError(
                {"branch": "A branch is required for agents and branch managers."}
            )

        if branch is not None and not branch.is_active:
            raise serializers.ValidationError(
                {"branch": "Users cannot be assigned to an inactive branch."}
            )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")

        return User.objects.create_user(
            password=password,
            **validated_data,
        )