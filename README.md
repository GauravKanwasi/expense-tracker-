# Expense Tracker API

A simple FastAPI backend for tracking personal income, expenses, categories, monthly budgets, and spending analytics.

## Architecture

~~~mermaid
flowchart LR
    Frontend[React or Vite frontend] -->|JSON and Bearer token| API[FastAPI API]
    API --> ORM[SQLAlchemy ORM]
    ORM --> DB[(PostgreSQL)]
~~~

The frontend is the next major step. Until then, Swagger at `/docs` is the interactive client for the backend.

## Quick navigation

- [What works now](#what-works-now)
- [Run locally](#run-locally)
- [Use the interactive API docs](#use-the-interactive-api-docs)
- [API endpoints](#api-endpoints)
- [Copy-ready examples](#copy-ready-examples)
- [Test the backend](#test-the-backend)
- [Security and production checklist](#security-and-production-checklist)
- [Next steps](#next-steps)

## What works now

- JWT authentication with protected routes.
- User registration and current-user lookup.
- User-owned categories with duplicate-name protection.
- Transaction create, list, filter, update, and delete.
- Transaction filters for type, category, date range, and pagination.
- One monthly budget per user and month.
- Analytics for totals and totals grouped by category.
- Ownership checks so one user cannot read or change another user data.
- Request validation for email, password length, positive amounts, dates, and budget months.
- Local CORS support for a Vite or React frontend on port 5173.
- Automated API tests.

## Project structure

~~~text
app/
|-- main.py                    App entry point, routers, CORS, health check
|-- database.py                Database engine and session dependency
|-- model.py                   SQLAlchemy database models
|-- schemas.py                 Pydantic request and response schemas
|-- security.py                Password hashing and JWT authentication
|-- routes/
|   |-- users.py               Registration and current user
|   |-- auth.py                Login
|   |-- categories.py          Category CRUD
|   |-- transactions.py        Transaction CRUD and filters
|   |-- budgets.py             Monthly budget CRUD
|   |-- analytics.py           Summary and category analytics
|   `-- inti.py                Unused placeholder kept for now
tests/
|-- conftest.py                Isolated test database and test client
`-- test_api.py                API behavior tests
.env.example                  Safe environment variable template
pytest.ini                    Pytest configuration
requirements.txt              Runtime dependencies
requirements-dev.txt          Development and test dependencies
~~~

## Run locally

### Prerequisites

Install Python 3.12 or newer and PostgreSQL. Create a PostgreSQL database named `expense_tracker`, then put your local database password in `.env`.

These commands are for PowerShell.

~~~powershell
Set-Location "D:\class\Project\expense traker"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
~~~

If PowerShell blocks virtual-environment activation, run this once in the same PowerShell window:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
~~~

Keep the terminal running while using the API. The server should show:

~~~text
Uvicorn running on http://127.0.0.1:8000
~~~

Open these pages in your browser:

- [API home](http://127.0.0.1:8000/)
- [Interactive Swagger docs](http://127.0.0.1:8000/docs)
- [OpenAPI JSON](http://127.0.0.1:8000/openapi.json)
- [Health check](http://127.0.0.1:8000/health)

## Use the interactive API docs

Swagger is the easiest way to test the backend without writing frontend code.

1. Open http://127.0.0.1:8000/docs.
2. Open `POST /users/`, click **Try it out**, and register a user.
3. Open `POST /auth/login`, enter the same email in the `username` field, enter the password, and execute.
4. Copy the `access_token` from the response.
5. Click **Authorize** at the top of the page.
6. Enter the token in the value field and authorize.
7. Test the locked categories, transactions, budgets, and analytics endpoints.

The login endpoint uses the OAuth2 form field name `username` for Swagger compatibility. The value should still be your email address.

Suggested test order:

~~~text
POST /users/                  Register
POST /auth/login              Login and copy token
GET  /users/me                 Confirm authentication
POST /categories/             Create a category
POST /transactions/            Add income or expense
POST /budgets/                Add a monthly budget
GET  /analytics/summary       See totals
GET  /analytics/by-category   See category totals
~~~

## API endpoints

All endpoints marked with a lock require a Bearer token.

| Area | Method | Path | Purpose | Auth |
| --- | --- | --- | --- | --- |
| System | GET | `/` | Confirm the API is running | No |
| System | GET | `/health` | Health check | No |
| Users | POST | `/users/` | Register a user | No |
| Users | GET | `/users/me` | Get the logged-in user | Yes |
| Auth | POST | `/auth/login` | Log in and receive a JWT | No |
| Categories | GET | `/categories/` | List your categories | Yes |
| Categories | POST | `/categories/` | Create a category | Yes |
| Categories | GET | `/categories/{category_id}` | Get one category | Yes |
| Categories | PUT | `/categories/{category_id}` | Rename a category | Yes |
| Categories | DELETE | `/categories/{category_id}` | Delete an unused category | Yes |
| Transactions | GET | `/transactions/` | List and filter transactions | Yes |
| Transactions | POST | `/transactions/` | Create a transaction | Yes |
| Transactions | GET | `/transactions/{transaction_id}` | Get one transaction | Yes |
| Transactions | PUT | `/transactions/{transaction_id}` | Update a transaction | Yes |
| Transactions | DELETE | `/transactions/{transaction_id}` | Delete a transaction | Yes |
| Budgets | GET | `/budgets/` | List monthly budgets | Yes |
| Budgets | POST | `/budgets/` | Create a monthly budget | Yes |
| Budgets | GET | `/budgets/{budget_id}` | Get one budget | Yes |
| Budgets | PUT | `/budgets/{budget_id}` | Update a budget | Yes |
| Budgets | DELETE | `/budgets/{budget_id}` | Delete a budget | Yes |
| Analytics | GET | `/analytics/summary` | Income, expenses, and balance | Yes |
| Analytics | GET | `/analytics/by-category` | Totals grouped by category | Yes |

## Copy-ready examples

### Register

~~~json
{
  "name": "Sapna",
  "email": "sapna@example.com",
  "password": "strongpassword123"
}
~~~

### Create a category

~~~json
{
  "name": "Food"
}
~~~

Use the returned category `id` when creating a transaction. Do not assume that Food is category ID 1; IDs depend on the database.

### Create a transaction

~~~json
{
  "category_id": 5,
  "amount": 250,
  "type": "expense",
  "description": "Lunch",
  "date": "2026-08-29T12:00:00"
}
~~~

`category_id` must belong to the logged-in user. `amount` must be greater than zero and `type` must be either `income` or `expense`.

### Create a monthly budget

~~~json
{
  "year": 2026,
  "month": 8,
  "amount": 10000
}
~~~

Only one budget is allowed for each user, year, and month.

### Filter transactions

~~~text
GET /transactions/?type=expense
GET /transactions/?category_id=5
GET /transactions/?start_date=2026-08-01&end_date=2026-08-31
GET /transactions/?skip=0&limit=20
GET /transactions/?type=expense&category_id=5&start_date=2026-08-01&end_date=2026-08-31
~~~

`limit` is capped at 100. Dates use `YYYY-MM-DD` format in query parameters.

### Read analytics

~~~text
GET /analytics/summary?start_date=2026-08-01&end_date=2026-08-31
GET /analytics/by-category?start_date=2026-08-01&end_date=2026-08-31
~~~

## Interactive walkthrough

Use this checklist while testing in Swagger:

- [ ] Start the server with Uvicorn.
- [ ] Open `/docs`.
- [ ] Register a new user.
- [ ] Log in and authorize Swagger.
- [ ] Confirm `/users/me` returns your user.
- [ ] Create at least two categories.
- [ ] Add one income transaction.
- [ ] Add one expense transaction.
- [ ] List transactions and try a filter.
- [ ] Create a monthly budget.
- [ ] Read the analytics summary.
- [ ] Read analytics by category.
- [ ] Update and delete a transaction.
- [ ] Try deleting a category that has a transaction and confirm it is rejected.

## Common responses

| Status | Meaning | Typical cause |
| --- | --- | --- |
| 200 | Success | Request completed |
| 201 | Created | Resource created, where applicable |
| 400 | Bad request | Duplicate data, invalid filter, or protected category deletion |
| 401 | Unauthorized | Missing, expired, or invalid token |
| 404 | Not found | Resource does not belong to the logged-in user or does not exist |
| 422 | Validation error | Request body or query parameter has the wrong value |

## Test the backend

Run this from the project folder with the virtual environment active:

~~~powershell
pytest -q -p no:cacheprovider
~~~

The tests use an isolated SQLite database, so normal test runs do not change your PostgreSQL data. The `-p no:cacheprovider` option avoids a local pytest cache permission warning on this machine.

## Security and production checklist

The backend is in good shape for local development and frontend integration. Before deploying it publicly, complete these items:

- [ ] Replace any previously exposed database password or JWT secret.
- [ ] Put real secrets only in environment variables; never commit `.env`.
- [ ] Replace `Base.metadata.create_all()` with Alembic migrations.
- [ ] Change money columns from floating point to a fixed-precision `Decimal` or `Numeric` type.
- [ ] Add rate limiting and account lockout protection to login.
- [ ] Run behind HTTPS and add production security headers.
- [ ] Set CORS to the exact deployed frontend URL.
- [ ] Use a production process manager and database backups.
- [ ] Add logging and monitoring without logging passwords or tokens.

`.env.example` contains placeholders only. Create a private `.env` file from it before running the API.

## Next steps

1. Build the React or Vite frontend against the documented endpoints.
2. Store the JWT safely in the frontend and send it as `Authorization: Bearer <token>`.
3. Build login, dashboard, transactions, categories, budgets, and analytics screens.
4. Add Alembic migrations and fixed-precision money handling before deployment.
5. Add deployment configuration, HTTPS, backups, rate limiting, and monitoring.

## License

License: to be decided.
