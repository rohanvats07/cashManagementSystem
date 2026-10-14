from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from accounts.models import User
from branches.models import Branch
from customers.models import Customer


class CustomerAPITests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            code="CUST-BR01",
            name="Customer Test Branch",
            city="Gurugram",
            state="Haryana",
        )
        self.other_branch = Branch.objects.create(
            code="CUST-BR02",
            name="Other Test Branch",
            city="Delhi",
            state="Delhi",
        )

        self.manager = User.objects.create_user(
            username="customer_manager",
            password="Manager-Test-Password-2026!",
            role=User.Role.BRANCH_MANAGER,
            branch=self.branch,
        )
        self.agent = User.objects.create_user(
            username="customer_agent",
            password="Agent-Test-Password-2026!",
            role=User.Role.COLLECTION_AGENT,
            branch=self.branch,
        )
        self.other_agent = User.objects.create_user(
            username="other_customer_agent",
            password="Agent-Test-Password-2026!",
            role=User.Role.COLLECTION_AGENT,
            branch=self.other_branch,
        )

        self.customer = Customer.objects.create(
            full_name="Test Customer",
            phone="9876500001",
            branch=self.branch,
            assigned_agent=self.agent,
        )

    def test_agent_sees_only_assigned_customers(self):
        Customer.objects.create(
            full_name="Other Agent Customer",
            phone="9876500002",
            branch=self.branch,
            assigned_agent=self.other_agent,
        )

        self.client.force_authenticate(user=self.agent)
        response = self.client.get(reverse("customer-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["customer_code"],
            self.customer.customer_code,
        )

    def test_branch_manager_sees_branch_customers(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.get(reverse("customer-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_agent_cannot_create_customer(self):
        self.client.force_authenticate(user=self.agent)

        response = self.client.post(
            reverse("customer-list"),
            {
                "full_name": "Unauthorized Customer",
                "phone": "9876500003",
                "branch": self.branch.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_cannot_assign_customer_to_other_branch(self):
        self.client.force_authenticate(user=self.manager)

        response = self.client.post(
            reverse("customer-list"),
            {
                "full_name": "Wrong Branch Customer",
                "phone": "9876500004",
                "branch": self.other_branch.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_customer_code_is_generated(self):
        self.assertTrue(self.customer.customer_code.startswith("CUS-"))