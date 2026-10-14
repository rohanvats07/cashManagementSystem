# Cash Management & Reconciliation System (CMRS)

A full-stack application for managing cash collections, branch reconciliation, bank deposits, and settlement tracking for a lending or fintech company.

## 1. Overview

CMRS tracks the lifecycle of customer loan repayments across collection agents, branches, and bank deposits.

**Business workflow**

`Customer → Collection Agent → Branch → Bank Deposit → Company Account`

The system is designed to provide visibility into collections, cash discrepancies, outstanding balances, deposit records, and settlement status.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, Vite, JavaScript |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL |
| Authentication | JWT using Simple JWT |
| Authorization | Role-based access control |
| API documentation | OpenAPI, Swagger UI |
| Frontend routing | React Router |
| API requests | Axios |
| Server-state management | TanStack Query |
| Testing | Django and DRF automated tests |
| Version control | Git and GitHub |

## 3. User Roles

### Administrator
- Create and manage branches.
- Create application users and assign roles.
- Access administrative functionality.

### Collection Agent
- Access the assigned branch's information.
- View assigned customers and loans (planned).
- Record customer repayments and generate receipts (planned).
- Submit collected cash to the branch (planned).

### Branch Manager
- Access branch-level information.
- Review agent cash submissions (planned).
- Record discrepancies and approve or reject submissions (planned).
- Manage bank deposits and reconciliation workflows (planned).

### Auditor
- Read branch information across the system.
- Review authorized reports and audit history (planned).
- Does not receive branch-management write permissions.

Authorization is enforced by the backend API, not only by frontend visibility.

## 4. Current Implementation Status

### Implemented
- Django REST Framework backend foundation.
- PostgreSQL database configuration.
- Custom Django user model.
- Four application roles.
- JWT access and refresh token endpoints.
- Authenticated current-user endpoint.
- Branch model and REST API.
- Administrator-only branch writes.
- Branch-scoped branch visibility.
- Swagger API documentation.
- Health endpoint with database connectivity check.
- Initial automated authentication and permission tests.
- React dashboard shell.
- Digital Payments — Coming Soon UI.

### Planned
- Customer and loan management.
- Loan repayment schedules and outstanding balance calculation.
- Cash collection and partial repayment processing.
- Unique repayment receipts and duplicate protection.
- Agent cash submissions.
- Branch reconciliation and discrepancy handling.
- Bank deposit and settlement tracking.
- Operational dashboards and reporting.
- Audit history for financial transactions.
- Payment gateway integration.

**Payment gateway status:** Not implemented. The current interface is a placeholder and does not process payments or move money.

## 5. Repository Structure

```text
cmrs/
├── backend/
│   ├── accounts/
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── branches/
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── common/
│   │   ├── migrations/
│   │   ├── permissions.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── config/
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── .env
│   ├── .env.example
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .env.local
│   ├── package.json
│   └── package-lock.json
├── .gitignore
└── README.md
```

Some generated files, such as `apps.py`, `asgi.py`, `wsgi.py`, and migration package files, are created automatically by Django or Vite.

### Backend file responsibilities

| File | Responsibility |
|---|---|
| `accounts/models.py` | Custom user model and application roles |
| `accounts/serializers.py` | User creation and profile serialization |
| `accounts/views.py` | Current-user and administrator user-creation APIs |
| `accounts/urls.py` | Authentication-related application routes |
| `accounts/admin.py` | User administration in Django Admin |
| `accounts/tests.py` | Authentication and role-permission tests |
| `branches/models.py` | Branch database model |
| `branches/serializers.py` | Branch request validation and response formatting |
| `branches/views.py` | Branch CRUD endpoints and queryset scoping |
| `branches/urls.py` | Branch API routing |
| `branches/admin.py` | Branch administration in Django Admin |
| `common/permissions.py` | Reusable application permission classes |
| `common/views.py` | Health endpoint and database connectivity check |
| `common/urls.py` | Common API routes |
| `config/settings.py` | Installed apps, database, security and REST configuration |
| `config/urls.py` | Root API routing, JWT endpoints and Swagger |
| `manage.py` | Django management commands |

### Frontend file responsibilities

| File | Responsibility |
|---|---|
| `src/App.jsx` | Main dashboard shell and initial API health check |
| `src/App.css` | Dashboard layout, navigation, metric cards and payment placeholder styling |
| `src/index.css` | Global styles and base typography |
| `src/main.jsx` | React application entry point |
| `package.json` | Frontend dependencies and scripts |
| `.env.local` | Local frontend API base URL |

As the application grows, frontend pages, reusable components, API clients, route definitions, and authentication state will be separated into dedicated modules.

## 6. Prerequisites

Install the following:

- Python 3.10 or a compatible supported Python version.
- Node.js and npm.
- PostgreSQL.
- Git.

Check installations:

```powershell
python --version
node --version
npm --version
psql --version
```

The commands in this guide assume Windows PowerShell.

## 7. Backend Setup

### Step 1: Enter the backend directory

```powershell
cd backend
```

### Step 2: Create the virtual environment if necessary

```powershell
py -m venv .venv
```

### Step 3: Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

Alternatively, run the Python executable directly using `.venv\Scripts\python.exe`.

### Step 4: Install dependencies

Once the dependency file is available:

```powershell
python -m pip install -r requirements.txt
```

### Step 5: Configure environment variables

Copy `.env.example` to `.env` and replace the development placeholders with local values.

Required variables:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=cmrs_db
DB_USER=cmrs_app
DB_PASSWORD=replace-with-your-local-database-password
DB_HOST=127.0.0.1
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Never commit `.env` or expose production credentials.

### Step 6: Apply migrations

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Commit generated migration files to Git.

### Step 7: Create an administrator

```powershell
python manage.py createsuperuser
```

Set the account's CMRS role to `ADMIN` if it is not already assigned.

### Step 8: Start Django

```powershell
python manage.py runserver 8000
```

The backend is available at `http://localhost:8000`.

## 8. Frontend Setup

Open a separate terminal.

```powershell
cd frontend
npm install
```

Configure `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000/api
```

Start the frontend:

```powershell
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`.

The frontend needs the Django backend running to show a successful API health indicator.

## 9. API Reference

Base URL: `http://localhost:8000/api`

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health/` | Check API and database health |
| `POST` | `/auth/token/` | Obtain JWT tokens |
| `POST` | `/auth/token/refresh/` | Refresh an access token |
| `GET` | `/auth/me/` | Retrieve authenticated user profile |
| `POST` | `/auth/users/` | Create a user as an administrator |
| `GET` | `/branches/` | List authorized branches |
| `POST` | `/branches/` | Create a branch as an administrator |
| `GET` | `/branches/{id}/` | Retrieve an authorized branch |
| `PUT` | `/branches/{id}/` | Replace a branch as an administrator |
| `PATCH` | `/branches/{id}/` | Update a branch as an administrator |
| `DELETE` | `/branches/{id}/` | Delete an eligible branch as an administrator |
| `GET` | `/schema/` | Retrieve OpenAPI schema |
| `GET` | `/docs/` | Open Swagger UI |

Except for explicitly public endpoints, business APIs require authentication.

### JWT authentication example

Request:

```http
POST /api/auth/token/
Content-Type: application/json
```

```json
{
    "username": "your_username",
    "password": "your_password"
}
```

Use the returned access token for authenticated requests:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Branch creation example

```http
POST /api/branches/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

```json
{
    "code": "BR001",
    "name": "Gurugram Branch",
    "address": "Example branch address",
    "city": "Gurugram",
    "state": "Haryana",
    "pincode": "122001",
    "is_active": true
}
```

### Interactive API documentation

- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

## 10. Database Design

The initial database contains two application entities.

### Branch

- Primary key: `id`
- Unique identifier: `code`
- Branch name, address, city, state and pincode.
- Active/inactive status.
- Creation and update timestamps.

### User

Extends Django's user model and includes:

- Username and password hash.
- Email and contact information.
- Application role.
- Optional foreign key to a branch.
- Active status and Django administrative permissions.
- Creation and update timestamps.

### Relationships

```text
Branch 1 ─────────── N User
```

A branch can have multiple users. A user can be assigned to one branch or remain unassigned, depending on their role.

Loan, repayment, reconciliation, deposit and settlement entities will be introduced in subsequent milestones.

## 11. Financial Data and Business Rules

The financial workflow will use decimal/numeric database types rather than floating-point arithmetic.

Planned safeguards include:

- Unique repayment reference numbers.
- Database transactions for repayment processing.
- Duplicate collection prevention.
- Separate expected, collected, branch-received, deposited and settled amounts.
- Expected-versus-actual reconciliation.
- Discrepancy records and explicit approval decisions.
- Protection against unauthorized changes to reconciled transactions.
- Audit history for financially significant actions.

These financial workflows are not yet implemented in the initial foundation.

## 12. Testing

Run backend checks:

```powershell
python manage.py check
python manage.py test
```

Build the frontend:

```powershell
cd frontend
npm run build
```

The automated tests cover authentication, branch visibility and role-based permissions. More tests will be added as the collection and reconciliation workflows are implemented.

## 13. Security and Configuration

- Keep secrets in environment variables.
- Never commit real passwords, API keys or database credentials.
- Use Django's password hashing and validation.
- Restrict API access with authentication and explicit permissions.
- Avoid exposing privileged user fields through public serializers.
- Use database constraints and transactions for financial operations.
- Disable Django debug mode and configure secure deployment settings in production.
- Use HTTPS and an appropriate token lifecycle in production.
- Apply database backups, monitoring and audit logging before production use.

## 14. Payment Gateway

Payment integration is deliberately deferred.

The frontend currently displays a Digital Payments — Coming Soon section. UPI processing, payment-provider callbacks, payment transaction storage and real-money processing are not implemented.

A future payment integration should support verified provider callbacks, idempotency, transaction references, settlement reconciliation and secure secret management.

## 15. Development Roadmap

1. Project foundation and PostgreSQL connectivity.
2. Authentication, roles and branch management.
3. Customer, loan and repayment-schedule management.
4. Cash collections, partial repayments and agent submissions.
5. Branch reconciliation and discrepancy handling.
6. Bank deposits and settlement tracking.
7. Role-specific dashboards and reports.
8. Automated testing and audit history.
9. Deployment, documentation and final demonstration.

## 16. Contributing

1. Create a feature branch.
2. Implement a focused change.
3. Add or update tests.
4. Run Django checks, backend tests and the frontend build.
5. Commit migrations and source files.
6. Open a pull request for review.

## License

Specify the project's license before distributing the software.
