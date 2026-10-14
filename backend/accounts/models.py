from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        COLLECTION_AGENT = "COLLECTION_AGENT", "Collection Agent"
        BRANCH_MANAGER = "BRANCH_MANAGER", "Branch Manager"
        AUDITOR = "AUDITOR", "Auditor"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.COLLECTION_AGENT,
        db_index=True,
    )

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )

    phone = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"