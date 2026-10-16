
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial CMRS administrator once."

    def handle(self, *args, **options):
        username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME")
        email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")

        if not all([username, email, password]):
            raise CommandError(
                "Bootstrap administrator environment variables are missing."
            )

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            raise CommandError(
                "This username already exists. Bootstrap stopped without "
                "changing the existing account."
            )

        user = User(
            username=username,
            email=email,
            role="ADMIN",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS("Initial administrator created successfully.")
        )
