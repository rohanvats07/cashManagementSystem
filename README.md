# Cash Management & Reconciliation System (CMRS)

A full-stack application for managing loan repayments collected in cash and tracking them through the lifecycle:

**Customer → Collection Agent → Branch → Bank Deposit → Company Account**

The application uses React/Vite, Django REST Framework, PostgreSQL, REST APIs, JWT authentication, and role-based access control (RBAC).

- [Hosted Application](https://cash-management-system-rosy.vercel.app/)

## Contents

- [Features](#features)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Roles](#roles)
- [Workflow](#workflow)
- [API overview](#api-overview)
- [Database concepts](#database-concepts)
- [Local setup](#local-setup)
- [Environment variables](#environment-variables)
- [API documentation](#api-documentation)
- [Demo Video](#Demo-Video)

## Features

### Customer and loan management
- Customer and loan APIs.
- Loan repayment schedules and EMI calculations.
- Repayment allocation to loan schedules.
- Loan and repayment information exposed through REST APIs.

### Cash collection
- Collection agents can record cash repayments.
- Partial repayments are supported.
- Unique receipt/reference numbers are generated.
- An idempotency key helps prevent duplicate collection creation when a request is retried.
- Collection records track loan/customer, amount, collector, date, and notes.

### Branch cash submissions
- Agents submit collected cash to their branch.
- Authorized branch managers/admins can accept or reject submissions and add review notes.
- Access is scoped by role and branch in the backend.

### Bank deposits and reconciliation
- Create a bank deposit from eligible accepted cash submissions.
- Record bank name, deposit date, bank reference, expected amount, and deposited amount.
- Reconcile a deposit against a company-account/bank-statement credit.
- Reconciliation outcomes include matched, short, excess, or discrepancy.
- Database uniqueness constraints help prevent duplicate deposit numbers and bank references.

### Authentication and payments
- JWT authentication using Django REST Framework Simple JWT.
- Role-based access control for admin, collection agent, branch manager, and auditor.
- The backend is the source of truth for permissions, validation, and financial calculations.
- **Digital payments are not implemented.** The UI shows “Digital Payments — Coming Soon”; no payment gateway or real-money processing is included.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React, JavaScript, Vite |
| UI/data fetching | CSS, Axios, React Query, React Router |
| Backend | Python, Django, Django REST Framework |
| Authentication | JWT / Simple JWT |
| Database | PostgreSQL |
| API | REST |
| Version control | Git and GitHub |

## Architecture

```text
React + Vite frontend
        | HTTPS / JSON REST API + JWT
        v
Django REST Framework backend
        | Django ORM
        v
PostgreSQL database
```

## Roles

- **ADMIN** — administrative access across branches; can perform company-account reconciliation.
- **COLLECTION_AGENT** — records repayments and submits their own collected cash.
- **ADMIN / BRANCH_MANAGER** — reviews submissions and manages deposits for their assigned branch.

## Workflow

1. A customer and loan exist in the system.
2. A collection agent records a cash repayment against a loan.
3. The system creates a collection receipt and allocates the repayment to schedules according to the implemented rules.
4. The agent submits eligible collections to the branch.
5. An authorized branch manager/admin accepts or rejects the submission.
6. An authorized branch user creates a bank deposit from eligible accepted submissions.
7. The deposit is marked as deposited with bank, reference, amount, and date details.
8. An admin reconciles the deposit against the company-account/bank-statement credit.
9. The system records a matched, short, excess, or discrepancy result.

## API overview

Local backend base URL: `http://localhost:8000`; API prefix: `/api`.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/auth/token/` | Obtain JWT access/refresh tokens |
| `POST` | `/api/auth/token/refresh/` | Refresh an access token |
| `GET` | `/api/health/` | Health check |
| `GET` | `/api/me/` | Current authenticated user's profile and role |
| `GET`, `POST` | `/api/branches/` | List/create branches, subject to permissions |
| `GET`, `POST` | `/api/users/` | List/create users, subject to permissions |
| `GET`, `POST` | `/api/customers/` | List/create customers |
| `GET`, `POST` | `/api/loans/` | List/create loans |
| `GET`, `POST` | `/api/collections/` | List or record collections |
| `GET` | `/api/collections/{id}/` | Retrieve a collection |
| `GET`, `POST` | `/api/cash-submissions/` | List or create cash submissions |
| `GET` | `/api/cash-submissions/{id}/` | Retrieve a submission |
| `POST` | `/api/cash-submissions/{id}/review/` | Accept/reject a submission |
| `GET`, `POST` | `/api/bank-deposits/` | List/create bank deposits |
| `GET` | `/api/bank-deposits/{id}/` | Retrieve a deposit |
| `POST` | `/api/bank-deposits/{id}/mark-deposited/` | Record bank deposit details |
| `POST` | `/api/bank-deposits/{id}/reconcile/` | Reconcile a deposit against a statement credit |

### Frontend request payloads

Payloads expected by the frontend integration.

- Create collection: `loan`, `amount`, `idempotency_key`, `notes`
- Create cash submission: `collection_ids`
- Review submission: `decision` (`accept` or `reject`), `review_notes`
- Create bank deposit: `submission_ids`
- Mark deposited: `bank_name`, `bank_reference`, `deposited_amount`, `deposit_date`
- Reconcile deposit: `statement_reference`, `statement_date`, `credited_amount`, `notes`

## Database concepts

Main domain entities include:

- **User** — identity, role, and optional branch assignment.
- **Branch** — branch identity and code.
- **Customer** — customer details and assignment/access relationships.
- **Loan** — loan terms and current loan information.
- **Repayment schedule** — due installments and principal/interest components.
- **CashCollection** — receipt, collector, loan/customer, amount, date, and idempotency key.
- **CollectionAllocation** — allocation of a collection to repayment schedules.
- **CashSubmission** — agent-to-branch submission and review status.
- **CashSubmissionItem** — collections included in a submission.
- **BankDeposit** — deposit bank details, expected/deposited amounts, and status.
- **BankDepositItem** — submissions included in a deposit.
- **BankReconciliation** — statement credit, outcome, notes, and reviewer.

## Local setup

### Prerequisites

Install Python (compatible with backend dependencies), Node.js/npm, PostgreSQL, and Git.

### 1. Clone the repository

```powershell
git clone <GITHUB_REPOSITORY_URL>
cd cashManagementSystem
```

Replace the placeholder with your actual repository URL.

Expected top-level layout:

```text
cashManagementSystem/
├── backend/
│   ├── manage.py
│   ├── config/
│   ├── common/
│   ├── accounts/
│   ├── branches/
│   ├── customers/
│   ├── loans/
│   └── cash_collections/
└── frontend/
    ├── package.json
    ├── index.html
    └── src/
```

### 2. Create PostgreSQL database

The local development database has been named `cmrs_db`, with an application user `cmrs_app`. Example SQL (run as a PostgreSQL administrator and replace the password):

```sql
CREATE DATABASE cmrs_db;
CREATE USER cmrs_app WITH PASSWORD 'REPLACE_WITH_A_LOCAL_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE cmrs_db TO cmrs_app;
```

### 3. Set up backend

In PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install dependencies from the repository's dependency file, if present:

```powershell
pip install -r requirements.txt
```

Create `backend/.env` using the `.env.example`

### 4. Apply migrations and create users

From `backend`:

```powershell
python manage.py check
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run backend

From `backend`:

```powershell
python manage.py runserver 8000
```

Backend URL: `http://localhost:8000`.

### 6. Set up and run frontend

Open another PowerShell window:

```powershell
cd frontend
npm install
```

Create `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api
```

Start Vite:

```powershell
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.


## Environment variables

### Frontend

| Variable | Purpose | Local example |
|---|---|---|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api` |

### Backend

Configure variables that the actual `backend/config/settings.py` reads. Common production configuration includes:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Private Django signing key |
| `DEBUG` | Must be `False` in production |
| `ALLOWED_HOSTS` | Permitted backend hostnames |
| `DATABASE_URL` or database-specific variables | PostgreSQL connection |
| `CORS_ALLOWED_ORIGINS` | Trusted frontend origins, if configured in settings |

## API documentation

When the backend is running:

- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

Use these pages to inspect request schemas, responses, and operations. Frontend payloads must match backend serializers.

## Demo Video
[Watch the Demo Video](https://drive.google.com/drive/folders/198jXBCW2KoF9bVgIOXzQysGbJpnEmOc-?usp=sharing)
