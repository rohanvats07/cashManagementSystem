# Cash Management & Reconciliation System (CMRS)

A full-stack application for managing loan repayments collected in cash and tracking them through the lifecycle:

**Customer → Collection Agent → Branch → Bank Deposit → Company Account**

The application uses React/Vite, Django REST Framework, PostgreSQL, REST APIs, JWT authentication, and role-based access control (RBAC).

> **Status note:** The core workflow has been implemented and exercised locally. Complete the verification checklist below before describing every assignment requirement as finished. In particular, confirm dashboard/report filters, over-collection behavior, discrepancy reporting, and production security.

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
- [Verification checklist](#verification-checklist)
- [Deployment](#deployment)
- [Test credentials](#test-credentials)
- [Five-minute demo video](#five-minute-demo-video)

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

Business rules, authorization, validation, and financial calculations must be enforced on the backend, not trusted to browser-side code.

## Roles

- **ADMIN** — administrative access across branches; can perform company-account reconciliation.
- **COLLECTION_AGENT** — records repayments and submits their own collected cash.
- **BRANCH_MANAGER** — reviews submissions and manages deposits for their assigned branch.
- **AUDITOR** — read-oriented visibility into permitted records.

Verify exact permissions using separate demo accounts. Do not use real customer or employee accounts for a public demo.

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

Confirm exact request/response schemas in the running API docs; permissions and validation apply to each endpoint.

### Frontend request payloads

These are the payloads expected by the frontend integration. Verify them against the current backend serializers before deployment:

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

Monetary values must use `DecimalField`/PostgreSQL numeric types and decimal arithmetic. Do not use binary floating-point arithmetic for financial calculations.

## Local setup

### Prerequisites

Install Python (compatible with backend dependencies), Node.js/npm, PostgreSQL, and Git.

### 1. Clone the repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
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

Depending on PostgreSQL version and ownership/schema permissions, additional privileges on the `public` schema may be required. Never commit the real password.

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

Create `backend/.env` using the variable names actually read by `backend/config/settings.py`. At minimum, production/local configuration commonly includes a Django secret, debug flag, allowed hosts, and PostgreSQL connection settings. Example only:

```dotenv
SECRET_KEY=replace_with_a_long_random_secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Do not blindly add environment variable names that the settings module does not read. If settings use individual database variables, configure those; if they use `DATABASE_URL`, configure that instead. Keep `.env` out of Git.

### 4. Apply migrations and create users

From `backend`:

```powershell
python manage.py check
python manage.py migrate
python manage.py createsuperuser
```

If tests are included, run:

```powershell
python manage.py test
```

Use the user-management API or Django admin to create separate demo users with appropriate roles and branch assignments.

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

Before deploying, run a production build and fix all errors:

```powershell
npm run build
```

A successful local development session does not guarantee a successful production build.

## Environment variables

### Frontend

| Variable | Purpose | Local example |
|---|---|---|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000/api` |

Any `VITE_` variable is bundled into client-side code. Never put secrets, database credentials, or private API keys in frontend environment variables.

### Backend

Configure variables that the actual `backend/config/settings.py` reads. Common production configuration includes:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Private Django signing key |
| `DEBUG` | Must be `False` in production |
| `ALLOWED_HOSTS` | Permitted backend hostnames |
| `DATABASE_URL` or database-specific variables | PostgreSQL connection |
| `CORS_ALLOWED_ORIGINS` | Trusted frontend origins, if configured in settings |

This list is a deployment checklist, not a guarantee that every variable is currently wired into the project. Confirm settings before deployment. Keep secrets out of GitHub and rotate any secret accidentally committed.

## API documentation

When the backend is running:

- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

Use these pages to inspect request schemas, responses, and operations. Frontend payloads must match backend serializers.

## Verification checklist

### Authentication and permissions
- [ ] Unauthenticated requests cannot access protected data.
- [ ] Admin, collection agent, branch manager, and auditor permissions work as intended.
- [ ] Agents cannot access or submit another agent's collections.
- [ ] Branch managers cannot access or change another branch's restricted data.
- [ ] Auditors cannot perform write actions.
- [ ] Invalid/expired tokens are handled safely.

### Collections and loan accounting
- [ ] A normal repayment creates a unique receipt.
- [ ] A partial repayment updates schedules and outstanding values correctly.
- [ ] Repeating a request with the same idempotency key does not create a duplicate.
- [ ] Over-collection is rejected or handled under an explicitly documented business rule.
- [ ] Financial values use decimal arithmetic.
- [ ] Repayment history and outstanding loan amount are presented accurately.

### Branch submissions
- [ ] Agents can submit only eligible collections assigned to them.
- [ ] Branch managers can review submissions only for their branch.
- [ ] Rejected submissions cannot enter a bank deposit.
- [ ] Expected-versus-actual differences can be explained and recorded.
- [ ] Reviewed/reconciled transactions cannot be modified by unauthorized API calls.

### Bank deposits and reconciliation
- [ ] Deposits contain only eligible accepted submissions.
- [ ] Duplicate bank references are rejected with a clear API error.
- [ ] Matched, short, excess, and discrepancy scenarios work.
- [ ] A deposit cannot be reconciled more than once unless explicitly allowed by the business rules.
- [ ] Failed/delayed settlement is represented or documented as a limitation.

### Dashboard and release
- [ ] Expected collections, total collected, cash held by agents, branch cash received, bank deposits, settled amount, outstanding amount, and discrepancies are available or documented as not implemented.
- [ ] Date, branch, agent, and status filters work where required.
- [ ] `python manage.py check` passes and backend tests pass.
- [ ] `npm run build` passes.
- [ ] Production `DEBUG=False`; secrets are not committed.
- [ ] CORS permits only the deployed frontend origin.
- [ ] Database migrations run successfully on the hosted database.
- [ ] Demo credentials use synthetic data and are safe to share.
- [ ] Hosted URL and the required explanation video are ready.

Do not mark a feature complete just because a model or endpoint exists. Verify its end-to-end UI, API behavior, permissions, and edge cases.

## Deployment

GitHub stores the source code; it does not host the complete Django + PostgreSQL application by itself.

Recommended deployment split:

1. **Frontend:** Vercel (or Netlify) for the React/Vite static frontend.
2. **Backend:** Render web service for Django REST Framework.
3. **Database:** Managed PostgreSQL, for example Render PostgreSQL.

GitHub Pages can host static frontend files, but it cannot run the Django backend or supply the PostgreSQL database. For this project, use GitHub as the source repository and deploy the frontend/backend/database to hosting services.

Official guides:
- Render Django: https://render.com/docs/deploy-django
- Render PostgreSQL: https://render.com/docs/postgresql
- Vercel + Vite: https://vercel.com/docs/frameworks/frontend/vite

Before production deployment, configure the production API URL, `DEBUG=False`, `ALLOWED_HOSTS`, CORS/CSRF settings as applicable, HTTPS, secret environment variables, database migrations, and a production WSGI server. Confirm current plan pricing, idle/sleep behavior, data retention, and backups before relying on a host.

## Known scope and follow-up checks

This is an assignment/demo system, not a production financial platform. Explicitly verify the following against the final code and UI:

1. Dashboard metrics and date/branch/agent/status filters required by the assignment.
2. Explicit over-collection handling and documented business rule.
3. Cash discrepancy amount/notes and expected-versus-actual review workflow.
4. Repayment history and outstanding-balance presentation.
5. Failed/delayed settlement tracking.
6. Tests preventing unauthorized changes to reviewed/reconciled transactions.
7. Production security, automated tests, monitoring, and deployment.
8. Test credentials for every role.

## Test credentials

Create dedicated demo users and replace the placeholders below before submission. Do not publish real credentials or a production administrator account.

| Role | Username | Password |
|---|---|---|
| Admin | `REPLACE_WITH_DEMO_ADMIN_USERNAME` | `REPLACE_WITH_DEMO_ADMIN_PASSWORD` |
| Collection agent | `REPLACE_WITH_AGENT_USERNAME` | `REPLACE_WITH_AGENT_PASSWORD` |
| Branch manager | `REPLACE_WITH_MANAGER_USERNAME` | `REPLACE_WITH_MANAGER_PASSWORD` |
| Auditor | `REPLACE_WITH_AUDITOR_USERNAME` | `REPLACE_WITH_AUDITOR_PASSWORD` |

Use synthetic customer and loan data only.

## License

Add a license if you intend to distribute or reuse this project publicly. Otherwise, follow the assignment and repository owner's terms.
