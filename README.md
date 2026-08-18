# 💰 Expense Tracker API

A real-world **Expense Tracker REST API** built as a project-first learning exercise — concepts are learned by implementing them, rather than studying theory first.

> 🚧 **Status: In Active Development**
> Core authentication and category management are complete. Transactions, budgets, analytics, and the frontend are in progress. See the [Roadmap](#-roadmap) below for exact progress.

---

## 📐 Architecture

```
React Frontend
      │
      │ HTTPS / REST API
      ▼
FastAPI Backend
      │
      ▼
SQLAlchemy
      │
      ▼
PostgreSQL
```

Local development currently runs over plain HTTP for simplicity:

```
http://127.0.0.1:8000
```

Production will sit behind a reverse proxy (Caddy/Nginx) handling TLS, HTTP → HTTPS redirects, and security headers.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| Server | Uvicorn |
| ORM | SQLAlchemy |
| Database | PostgreSQL 18 |
| DB Driver | psycopg |
| Validation | Pydantic / pydantic-settings |
| Password Hashing | pwdlib (Argon2) |
| Auth | PyJWT + OAuth2PasswordBearer |
| Forms | python-multipart |
| Email Validation | email-validator |
| Docs | Swagger / OpenAPI |
| Frontend (planned) | React + Vite |

---

## ✨ Features

### ✅ Implemented
- **User registration** with Argon2 password hashing
- **JWT-based authentication** via OAuth2 password flow
- **Protected routes** using `get_current_user` dependency
- **Category CRUD** — full create, read, update, delete, scoped per authenticated user

### 🚧 In Progress
- **Transactions** — income/expense entries linked to categories (next up)

### 📋 Planned
- Transaction filtering (date, category, type)
- Pagination
- Budgets
- Analytics dashboard endpoints
- Automated tests
- React frontend
- Production deployment with HTTPS

---

## 📁 Project Structure

```
expense-tracker/
│
├── app/
│   ├── main.py            # FastAPI app entrypoint
│   ├── database.py        # SQLAlchemy engine/session setup
│   ├── model.py            # ORM models
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── security.py         # Password hashing, JWT, auth dependency
│   │
│   └── routes/
│       ├── users.py         # Registration, current user
│       ├── auth.py          # Login (OAuth2 + JWT)
│       ├── categories.py    # Category CRUD
│       ├── transactions.py  # 🚧 Coming soon
│       └── budgets.py       # 📋 Planned
│
├── .env                  # Environment variables (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/GauravKanwasi/expense-tracker-.git
cd expense-tracker-
```

### 2. Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> If PowerShell blocks activation:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> ```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/expense_tracker
JWT_SECRET_KEY=YOUR_SECRET
```
> ⚠️ Never commit `.env` — it's already in `.gitignore`.

### 5. Set up PostgreSQL
Create a database named `expense_tracker` on your local PostgreSQL instance (default port `5432`).

### 6. Run the server
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

---

## 📖 API Documentation

Interactive API docs are auto-generated:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

### Authenticating in Swagger
Click **Authorize** and use:
- `username`: your registered **email**
- `password`: your password
- Leave `client_id` / `client_secret` blank

---

## 🔌 Current Endpoints

### Users
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/users/` | Register a new user | ❌ |
| GET | `/users/me` | Get current user profile | ✅ |

### Authentication
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/auth/login` | Log in and receive a JWT (OAuth2 form) | ❌ |

### Categories
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/categories/` | Create a category | ✅ |
| GET | `/categories/` | List your categories | ✅ |
| GET | `/categories/{id}` | Get a single category | ✅ |
| PUT | `/categories/{id}` | Update a category | ✅ |
| DELETE | `/categories/{id}` | Delete a category | ✅ |

### Transactions
🚧 Not yet implemented — planned endpoints:
```
POST   /transactions/
GET    /transactions/
GET    /transactions/{id}
PUT    /transactions/{id}
DELETE /transactions/{id}
```

---

## 🗺️ Roadmap

- [x] Project setup & virtual environment
- [x] FastAPI + PostgreSQL + SQLAlchemy wired up
- [x] User model & registration
- [x] Password hashing (Argon2)
- [x] Duplicate email handling
- [x] Login + JWT generation & verification
- [x] Protected `/users/me` endpoint
- [x] Category model
- [x] Category CRUD (create, read, update, delete)
- [ ] Transaction model & schema
- [ ] Transaction CRUD
- [ ] Transaction filtering (date / category / type)
- [ ] Pagination
- [ ] Budgets
- [ ] Analytics
- [ ] Validation & error handling polish
- [ ] Automated tests
- [ ] React frontend
- [ ] Production deployment
- [ ] HTTPS / TLS

---

## 🔒 Security Notes

- Passwords are hashed with **Argon2** before storage — plaintext passwords are never stored.
- Authentication uses **JWT** access tokens (30-minute expiry).
- All category (and future transaction/budget) data is scoped to the authenticated user — a user can only access their own data.
- `.env` is excluded from version control via `.gitignore`.

---

## 📄 License

Not yet decided — to be added before public release.

---

## 🙋 About This Project

This project is being built incrementally as a hands-on way to learn backend development with FastAPI, SQLAlchemy, and PostgreSQL — with a React frontend and full production deployment (HTTPS included) planned once the API is feature-complete.