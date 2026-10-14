from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from branches.models import Branch


class AuthenticationAndRoleTests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            code="BR001",
            name="Gurugram Branch",
            city="Gurugram",
            state="Haryana",
            pincode="122001",
        )

        self.other_branch = Branch.objects.create(
            code="BR002",
            name="Delhi Branch",
            city="Delhi",
            state="Delhi",
            pincode="110001",
        )

        self.admin = User.objects.create_user(
            username="cmrs_admin",
            password="Admin-Test-Password-2026!",
            role=User.Role.ADMIN,
        )

        self.agent = User.objects.create_user(
            username="agent_001",
            password="Agent-Test-Password-2026!",
            role=User.Role.COLLECTION_AGENT,
            branch=self.branch,
        )

        self.other_agent = User.objects.create_user(
            username="agent_002",
            password="Other-Agent-Test-Password-2026!",
            role=User.Role.COLLECTION_AGENT,
            branch=self.other_branch,
        )

        self.auditor = User.objects.create_user(
            username="auditor_001",
            password="Auditor-Test-Password-2026!",
            role=User.Role.AUDITOR,
        )

    def test_health_endpoint_is_public(self):
        response = self.client.get(reverse("common:health-check"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")

    def test_login_returns_jwt_tokens(self):
        response = self.client.post(
            reverse("token-obtain-pair"),
            {
                "username": "agent_001",
                "password": "Agent-Test-Password-2026!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("accounts:current-user"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agent_can_access_own_branch(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.get(reverse("branch-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["code"],
            "BR001",
        )

    def test_agent_cannot_access_another_branch(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.get(
            reverse("branch-detail", args=[self.other_branch.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agent_cannot_create_branch(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.post(
            reverse("branch-list"),
            {
                "code": "BR003",
                "name": "Jaipur Branch",
                "city": "Jaipur",
                "state": "Rajasthan",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_branch(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse("branch-list"),
            {
                "code": "BR003",
                "name": "Jaipur Branch",
                "city": "Jaipur",
                "state": "Rajasthan",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_auditor_can_read_but_not_modify_branches(self):
        self.client.force_authenticate(user=self.auditor)

        list_response = self.client.get(reverse("branch-list"))

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["results"]), 2)

        create_response = self.client.post(
            reverse("branch-list"),
            {
                "code": "BR004",
                "name": "Auditor Test Branch",
                "city": "Jaipur",
                "state": "Rajasthan",
            },
            format="json",
        )

        self.assertEqual(
            create_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )