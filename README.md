# Expense Sharing API
Expense Sharing API is a backend project for managing shared group expenses.

Users can register, create groups, add members, record expenses, track balances and create settlements between group members.

## Live API

- https://expense-sharing-api-mi1p.onrender.com

Interactive documentation: 

- https://expense-sharing-api-mi1p.onrender.com/docs

Alternative documentation:

- https://expense-sharing-api-mi1p.onrender.com/redoc

- https://expense-sharing-api-mi1p.onrender.com/health

## Features

- JWT authentication
- User registration and login
- Create groups
- Add and remove group members
- Create shared expenses
- Equal, exact, percentage split support
- Update and delete expenses
- Persist expense split rows for each participant
- List group expenses
- Get a single expense by ID
- Expense list filtering and pagination
- Create and list settlements
- Update and delete settlements
- Settlement list filtering and pagination
- Automated test coverage for core domains
- Settlement suggestions based on current group balances
- Rate limiting for authentication endpoints
- Group audit logs for expenses, settlements, and membership changes
- Recurring expense templates
- Create, list, and cancel recurring expenses
- Recurring expense processor job
- Manual command for processing due recurring expenses

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Pytest

## Project Structure
```txt
expense-sharing-api/
├── app/
│   ├── api/
│   │   ├── audit_logs.py
│   │   ├── auth.py
│   │   ├── balances.py
│   │   ├── deps.py
│   │   ├── expenses.py
│   │   ├── group_expenses.py
│   │   ├── group_members.py
│   │   ├── group_recurring_expenses.py
│   │   ├── group_settlements.py
│   │   ├── groups.py
│   │   ├── recurring_expenses.py
│   │   ├── settlement_suggestions.py
│   │   └── settlements.py
│   ├── core/
│   │   ├── config.py
│   │   ├── rate_limit.py
│   │   └── security.py
│   ├── jobs/
│   │   └── process_recurring_expenses.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── audit_log.py
│   │   ├── expense.py
│   │   ├── expense_splits.py
│   │   ├── group.py
│   │   ├── group_member.py
│   │   ├── recurring_expense.py
│   │   ├── recurring_expense_splits.py
│   │   ├── settlement.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── audit_log.py
│   │   ├── auth.py
│   │   ├── balance.py
│   │   ├── expense.py
│   │   ├── group.py
│   │   ├── group_member.py
│   │   ├── recurring_expense.py
│   │   ├── settlement.py
│   │   └── user.py
│   ├── services/
│   │   ├── audit_log_service.py
│   │   ├── auth_service.py
│   │   ├── balance_service.py
│   │   ├── exceptions.py
│   │   ├── expense_service.py
│   │   ├── group_member_service.py
│   │   ├── group_service.py
│   │   ├── helpers.py
│   │   ├── recurring_expense_service.py
│   │   ├── settlement_service.py
│   │   ├── settlement_suggestion_service.py
│   │   └── user_service.py
│   └── main.py
├── migrations/
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_audit_logs.py
│   ├── test_auth.py
│   ├── test_balances.py
│   ├── test_expenses.py
│   ├── test_group_members.py
│   ├── test_groups.py
│   ├── test_recurring_expenses.py
│   ├── test_settlement_suggestions.py
│   └── test_settlements.py
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

-------

## Setup

Clone the repository
```bash
git clone https://github.com/NikosKl/expense-sharing-api.git
cd expense-sharing-api
```

Choose one of the following ways to run the app:

- Local Development
- Docker Compose

### 1. Local Development

#### Create and activate a virtual environment
```bash
python -m venv venv

source venv/bin/activate # MacOS / Linux
venv\Scripts\activate # Windows
```
#### Install Dependencies
```bash
pip install -r requirements.txt
```
#### Environment Variables
Create a `.env` file in the project root.

```bash
cp .env.example .env
```
Copy and update the values to match your configuration. Both ``DATABASE_URL`` and ``TEST_DATABASE_URL`` should point to existing PostgreSQL databases.

#### Database migrations
To apply the existing migrations and create the database schema:
```bash
alembic upgrade head
```
#### Running the App
Make sure PostgreSQL is running before ``alembic upgrade head`` / ``fastapi dev``
```bash
fastapi dev app/main.py
```
Interactive docs:
```bash
http://127.0.0.1:8000/docs
```
### 2. Docker Compose

#### Create the Docker Compose environment file:

```bash
cp .env.compose.example .env.compose
```

Update the copied file with your local values before running Docker Compose.

#### Run full local stack with Compose:

```bash
docker compose --env-file .env.compose up --build
```

#### Run migrations inside the API container:

```bash
docker compose --env-file .env.compose exec api alembic upgrade head
```

#### Stop containers:

```bash
docker compose --env-file .env.compose down
```

#### Docker Notes

- `.env.compose` is used for Docker Compose
- Compose runs both the API and PostgreSQL containers
- PostgreSQL data is persisted using a named Docker volume
- `.env.compose` is ignored and should not be committed
- After `docker compose up`, migrations should be run from a second terminal while the containers are running

## Authentication
This API uses OAuth2 password flow with bearer token authentication.

### Login
`POST /auth/login`

The login endpoint expects OAuth2 form data, not JSON.

Important:
- the form field named `username` must contain the user's **email**
- the `password` field contains the user's password

Example form data:
```txt
username=test@example.com
password=secret123
```

On success, the API returns an access token. Use that token in subsequent authenticated requests with:
```http
Authorization: Bearer <access_token>
```

## Endpoints

### Auth
- ``POST /auth/register``
- ``POST /auth/login``
- ``GET /auth/me``

### Rate Limiting

The authentication endpoints are rate limited:

- `POST /auth/register`
- `POST /auth/login`

Default limits are configured with:

- `AUTH_REGISTER_RATE_LIMIT`
- `AUTH_LOGIN_RATE_LIMIT`

Exceeded limits return `429 Too Many Requests`.

### Groups
- ``POST /groups``
- ``GET /groups``
- ``GET /groups/{group_id}``

### Memberships
- ``POST /groups/{group_id}/members``
- ``GET /groups/{group_id}/members``
- ``DELETE /groups/{group_id}/members/{user_id}``

### Expenses
- ``POST /groups/{group_id}/expenses``
- ``GET /groups/{group_id}/expenses``
- ``GET /expenses/{expense_id}``
- ``PATCH /expenses/{expense_id}``
- ``DELETE /expenses/{expense_id}``

#### List group expenses query parameters

Used with:

`GET /groups/{group_id}/expenses`

| Parameter | Description |
| --- | --- |
| `limit` | Number of results to return. Defaults to `20`. |
| `offset` | Number of results to skip. Defaults to `0`. |
| `payer_id` | Filter expenses by payer user ID. |
| `date_from` | Return expenses on or after this datetime. |
| `date_to` | Return expenses on or before this datetime. |

### Balances 
- ``GET /groups/{group_id}/balances``

### Settlements
- ``POST /groups/{group_id}/settlements``
- ``GET /groups/{group_id}/settlements``
- ``GET /groups/{group_id}/settlement-suggestions``
- ``PATCH /settlements/{settlement_id}``
- ``DELETE /settlements/{settlement_id}``

#### List group settlements query parameters

Used with:

`GET /groups/{group_id}/settlements`

| Parameter     | Description                                    |
|---------------|------------------------------------------------|
| `limit`       | Number of results to return. Defaults to `20`. |
| `offset`      | Number of results to skip. Defaults to `0`.    |
| `payer_id`    | Filter settlements by payer user ID.           |
| `receiver_id` | Filter settlements by receiver user ID.        |

### Audit Logs

- ``GET /groups/{group_id}/audit-logs``

### Recurring Expenses

- ``POST /groups/{group_id}/recurring-expenses``
- ``GET /groups/{group_id}/recurring-expenses``
- ``DELETE /recurring-expenses/{recurring_expense_id}``

#### Recurring Expenses Processor

- Due recurring expenses can be processed manually with ``python -m app.jobs.process_recurring_expenses``
- The command checks active recurring expenses where ``next_run_at <= now``
- It creates real expenses, advances ``next_run_at``, and writes audit logs
- No scheduler is currently wired. A scheduler/cron can run this command later

## Running Tests

Run the full test suite:

```bash
pytest
```

## Settlement Notes

- Only the payer can create a settlement
- Payer must currently owe money
- Receiver must currently be owed money
- Settlement amount cannot exceed the allowed outstanding balance
- Settlement suggestions are read-only previews that show who should pay whom based on current balances. They do not create settlement records.

## Recurring Expenses Notes

- Recurring expenses are templates
- They do not affect balances directly
- When processed, they create real expenses with normal expense splits
- The generated expenses then affect balances like any other expense
- Canceling a recurring expense sets ``is_active`` to false

## Current Notes

- ``equal``, ``exact``, ``percentage`` splits are supported
- Expense splits are cascade-deleted when an expense is deleted
- Balances are computed on demand
- Settlements are not tied to a specific expense
- Audit logs are append-only and record key group events such as expense, settlement, and membership changes
