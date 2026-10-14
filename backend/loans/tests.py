from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from branches.models import Branch
from customers.models import Customer
from loans.models import Loan, RepaymentSchedule
from loans.services import calculate_emi


class LoanAPITests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            code="LOAN-BR01",
            name="Loan Test Branch",
            city="Gurugram",
            state="Haryana",
        )

        self.manager = User.objects.create_user(
            username="loan_manager",
            password="Manager-Test-Password-2026!",
            role=User.Role.BRANCH_MANAGER,
            branch=self.branch,
        )

        self.customer = Customer.objects.create(
            full_name="Loan Test Customer",
            phone="9876510001",
            branch=self.branch,
        )

        self.client.force_authenticate(user=self.manager)

    def test_zero_interest_emi(self):
        emi = calculate_emi(
            Decimal("12000.00"),
            Decimal("0"),
            12,
        )

        self.assertEqual(emi, Decimal("1000.00"))

    def test_emi_for_positive_interest(self):
        emi = calculate_emi(
            Decimal("100000.00"),
            Decimal("12"),
            12,
        )

        self.assertEqual(emi, Decimal("8884.88"))

    def test_create_loan_generates_schedule(self):
        response = self.client.post(
            reverse("loan-list"),
            {
                "customer": self.customer.id,
                "principal_amount": "100000.00",
                "annual_interest_rate": "12.0000",
                "tenor_months": 12,
                "disbursement_date": "2026-01-01",
                "first_due_date": "2026-02-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        loan = Loan.objects.get(loan_number=response.data["loan_number"])
        schedules = RepaymentSchedule.objects.filter(loan=loan)

        self.assertEqual(schedules.count(), 12)
        self.assertEqual(
            sum(
                (row.principal_due for row in schedules),
                Decimal("0.00"),
            ),
            Decimal("100000.00"),
        )
        self.assertEqual(
            sum(
                (row.total_due for row in schedules),
                Decimal("0.00"),
            ),
            loan.total_payable,
        )
        self.assertEqual(loan.created_by, self.manager)

    def test_schedule_endpoint_returns_installments(self):
        response = self.client.post(
            reverse("loan-list"),
            {
                "customer": self.customer.id,
                "principal_amount": "12000.00",
                "annual_interest_rate": "0",
                "tenor_months": 12,
                "disbursement_date": "2026-01-01",
                "first_due_date": "2026-02-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        loan_id = response.data["id"]
        schedule_response = self.client.get(
            reverse("loan-schedule", args=[loan_id])
        )

        self.assertEqual(
            schedule_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(schedule_response.data), 12)
        self.assertEqual(
            schedule_response.data[0]["total_due"],
            "1000.00",
        )

    def test_cannot_create_loan_for_inactive_customer(self):
        self.customer.is_active = False
        self.customer.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("loan-list"),
            {
                "customer": self.customer.id,
                "principal_amount": "10000.00",
                "annual_interest_rate": "12",
                "tenor_months": 12,
                "disbursement_date": "2026-01-01",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(Loan.objects.count(), 0)