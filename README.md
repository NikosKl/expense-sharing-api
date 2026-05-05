# Expense Sharing API
Expense Sharing API is a backend project for managing shared group expenses.

Users can register, create groups, add members, record expenses, track balances and create settlements between group members.

## Features

- JWT authentication
- User registration and login
- Create groups
- Add and remove group members
- Create shared expenses
- Equal split support
- Persist expense split rows for each participant
- List group expenses
- Get a single expense by ID
- Create and list settlements
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
Example:
```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/expense_sharing_db
JWT_SECRET_KEY=replace_with_a_long_secret
TEST_DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/test_expense_sharing_api
ENVIRONMENT=development
```
Update these values to match your configuration. Both ``DATABASE_URL`` and ``TEST_DATABASE_URL`` should point to existing PostgreSQL databases.

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
This API uses bearer token authentication.

### Login Note
`POST /auth/login`

The login endpoint uses FastAPI's OAuth2 password form.

Important:
- the OAuth2 form field named `username` must contain the user's **email**
- the `password` field contains the user's password

Example form data:
```txt
username=test@example.com
password=secret123
```
After login, include the token in the `Authorization` header:
```
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

### Group Memberships
- ``POST /groups/{group_id}/members``
- ``GET /groups/{group_id}/members``
- ``DELETE /groups/{group_id}/members/{user_id}``

### Expenses
- ``POST /groups/{group_id}/expenses``
- ``GET /groups/{group_id}/expenses``
- ``GET /expenses/{expense_id}``

### Balances 
- ``GET /groups/{group_id}/balances``

### Settlements
- ``POST /groups/{group_id}/settlements``
- ``GET /groups/{group_id}/settlements``

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

## Current MVP Notes

- Only ``equal`` split is supported
- Balances are computed on demand
- Settlements are not tied to a specific expense