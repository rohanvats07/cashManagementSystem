import uuid

from django.conf import settings
from django.db import models


def generate_customer_code():
    return f"CUS-{uuid.uuid4().hex[:12].upper()}"


class Customer(models.Model):
    customer_code = models.CharField(
        max_length=16,
        unique=True,
        default=generate_customer_code,
        editable=False,
    )
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="customers",
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_customers",
        limit_choices_to={"role": "COLLECTION_AGENT"},
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["branch", "is_active"]),
            models.Index(fields=["assigned_agent", "is_active"]),
        ]

    def __str__(self):
        return f"{self.customer_code} - {self.full_name}"