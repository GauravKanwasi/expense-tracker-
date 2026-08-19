<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:2c5364,100:00c9a7&height=200&section=header&text=Expense%20Tracker%20API&fontSize=45&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Learn%20Backend%20Dev%20by%20Building%20It&descAlignY=55&descSize=18" width="100%"/>

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=00C9A7&center=true&vCenter=true&width=600&lines=FastAPI+%2B+PostgreSQL+%2B+SQLAlchemy;JWT+Auth+with+Argon2+Hashing;Project-First+Learning+Approach;Building+in+Public+%F0%9F%9A%80" alt="Typing SVG" />

<br/>

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge&logo=python&logoColor=white)](https://www.sqlalchemy.org/)
[![JWT](https://img.shields.io/badge/Auth-JWT-black?style=for-the-badge&logo=jsonwebtokens)](https://jwt.io/)

![Status](https://img.shields.io/badge/status-active--development-yellow?style=flat-square)
![License](https://img.shields.io/badge/license-TBD-lightgrey?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/GauravKanwasi/expense-tracker-?style=flat-square)
![Repo Size](https://img.shields.io/github/repo-size/GauravKanwasi/expense-tracker-?style=flat-square)

</div>

---

### 🚧 Status: In Active Development

Core authentication and category management are complete. Transactions, budgets, analytics, and the frontend are in progress — see the [Roadmap](#️-roadmap) for exact progress.

**Overall completion**

![Progress](https://progress-bar.xyz/47/?title=core+api&width=300&color=00c9a7)

---

## 📐 Architecture

```mermaid
flowchart TD
    A[React Frontend] -->|HTTPS / REST API| B[FastAPI Backend]
    B --> C[SQLAlchemy ORM]
    C --> D[(PostgreSQL 18)]

    style A fill:#61dafb,color:#000
    style B fill:#009688,color:#fff
    style C fill:#D71F00,color:#fff
    style D fill:#336791,color:#fff
```

Local development currently runs over plain HTTP for simplicity:

```
http://127.0.0.1:8000
```

Production will sit behind a reverse proxy (Caddy/Nginx) handling TLS, HTTP → HTTPS redirects, and security headers.

---

## 🛠️ Tech Stack

<div align="center">

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

</div>

---

## ✨ Features

### ✅ Implemented
- 🔐 **User registration** with Argon2 password hashing
- 🪪 **JWT-based authentication** via OAuth2 password flow
- 🛡️ **Protected routes** using `get_current_user` dependency
- 🗂️ **Category CRUD** — full create, read, update, delete, scoped per authenticated user

### 🚧 In Progress
- 💸 **Transactions** — income/expense entries linked to categories (next up)

### 📋 Planned
- 🔍 Transaction filtering (date, category, type)
- 📄 Pagination
- 📊 Budgets
- 📈 Analytics dashboard endpoints
- 🧪 Automated tests
- ⚛️ React frontend
- ☁️ Production deployment with HTTPS

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

<details open>
<summary><b>1. Clone the repository</b></summary>

```bash
git clone https://github.com/GauravKanwasi/expense-tracker-.git
cd expense-tracker-
```
</details>

<details>
<summary><b>2. Create and activate a virtual environment</b></summary>

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> If PowerShell blocks activation:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> ```
</details>

<details>
<summary><b>3. Install dependencies</b></summary>

```bash
pip install -r requirements.txt
```
</details>

<details>
<summary><b>4. Configure environment variables</b></summary>

Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/expense_tracker
JWT_SECRET_KEY=YOUR_SECRET
```
> ⚠️ Never commit `.env` — it's already in `.gitignore`.
</details>

<details>
<summary><b>5. Set up PostgreSQL</b></summary>

Create a database named `expense_tracker` on your local PostgreSQL instance (default port `5432`).
</details>

<details>
<summary><b>6. Run the server</b></summary>

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
</details>

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
|---|---|---|:---:|
| `POST` | `/users/` | Register a new user | ❌ |
| `GET` | `/users/me` | Get current user profile | ✅ |

### Authentication
| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `POST` | `/auth/login` | Log in and receive a JWT (OAuth2 form) | ❌ |

### Categories
| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `POST` | `/categories/` | Create a category | ✅ |
| `GET` | `/categories/` | List your categories | ✅ |
| `GET` | `/categories/{id}` | Get a single category | ✅ |
| `PUT` | `/categories/{id}` | Update a category | ✅ |
| `DELETE` | `/categories/{id}` | Delete a category | ✅ |

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

- 🔑 Passwords are hashed with **Argon2** before storage — plaintext passwords are never stored.
- 🪪 Authentication uses **JWT** access tokens (30-minute expiry).
- 🛡️ All category (and future transaction/budget) data is scoped to the authenticated user — a user can only access their own data.
- 🙈 `.env` is excluded from version control via `.gitignore`.

---

## 📄 License

Not yet decided — to be added before public release.

---

## 🙋 About This Project

This project is being built incrementally as a hands-on way to learn backend development with FastAPI, SQLAlchemy, and PostgreSQL — with a React frontend and full production deployment (HTTPS included) planned once the API is feature-complete.

<div align="center">

### ⭐ If this project helps you learn, consider starring it!

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:00c9a7,100:0f2027&height=100&section=footer" width="100%"/>

</div>