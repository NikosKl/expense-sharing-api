# Expense Sharing API
Expense Sharing API is a backend project for managing shared expenses between users. It allows users to create groups, add expenses, split costs, and keep track of balances and settlements.

The project is built with FastAPI, PostgreSQL, and SQLAlchemy.

---

## Authentication
This API uses bearer token authentication.

### Login
`POST /auth/login`

The login endpoint uses FastAPI's OAuth2 password form.

Important:
- the OAuth2 form field named `username` must contain the user's **email**
- the `password` field contains the user's password

Example form data:

username=test@example.com
password=secret123

---

Detailed setup instructions and endpoint documentation will be added later.