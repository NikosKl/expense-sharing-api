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
- Equal, exact and percentage split support
- Update and delete expenses
- Persist expense split rows for each participant
- List group expenses
- Get a single expense by ID
- Expense list filtering and pagination
- Create and list settlements
- Update and delete settlements
- Settlement list filtering and pagination
- Automated test coverage for core domains

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
│   │   ├── auth.py
│   │   ├── balances.py
│   │   ├── deps.py
│   │   ├── expenses.py
│   │   ├── group_expenses.py
│   │   ├── group_members.py
│   │   ├── group_settlements.py
│   │   ├── groups.py
│   │   └── settlements.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── expense.py
│   │   ├── expense_splits.py
│   │   ├── group.py
│   │   ├── group_member.py
│   │   ├── settlement.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── balance.py
│   │   ├── expense.py
│   │   ├── group.py
│   │   ├── group_member.py
│   │   ├── settlement.py
│   │   └── user.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── balance_service.py
│   │   ├── exceptions.py
│   │   ├── expense_service.py
│   │   ├── group_member_service.py
│   │   ├── group_service.py
│   │   ├── helpers.py
│   │   ├── settlement_service.py
│   │   └── user_service.py
│   └── main.py
├── migrations/
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_auth.py
│   ├── test_balances.py
│   ├── test_expenses.py
│   ├── test_group_members.py
│   ├── test_groups.py
│   └── test_settlements.py
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

-------

## Setup

1. Clone the repository
```
git clone https://github.com/NikosKl/expense-sharing-api.git
cd expense-sharing-api
```
2. Create and activate a virtual environment
```bash
python -m venv venv

source venv/bin/activate # MacOS / Linux
venv\Scripts\activate # Windows
```
3. Install Dependencies
```bash
pip install -r requirements.txt
```
### Environment Variables
Create a `.env` file in the project root.

```bash
cp .env.example .env
```
Copy and update the values to match your configuration. Both ``DATABASE_URL`` and ``TEST_DATABASE_URL`` should point to existing PostgreSQL databases.

### Database migrations
To apply the existing migrations and create the database schema:
```bash
alembic upgrade head
```
### Running the App
Make sure PostgreSQL is running before ``alembic upgrade head`` / ``fastapi dev``
```bash
fastapi dev app/main.py
```
Interactive docs:
```bash
http://127.0.0.1:8000/docs
```

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

## Running Tests

Run the full test suite:

```bash
pytest
```

## Settlement Notes

- only the payer can create a settlement
- payer must currently owe money
- receiver must currently be owed money
- settlement amount cannot exceed the allowed outstanding balance

## Current Notes

- ``equal``, ``exact``, ``percentage`` splits are supported
- Balances are computed on demand
- Settlements are not tied to a specific expense