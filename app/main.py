from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import model
from .routes.users import router as users_router
from .routes.auth import router as auth_router
from .routes.categories import router as categories_router
from .routes.transactions import router as transactions_router
from .routes.budgets import router as budgets_router
from .routes.analytics import router as analytics_router
from .schemas import HealthResponse, MessageResponse


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Tracker API",
    version="1.0.0",
    description=(
        "A simple personal expense tracker API. "
        "Authenticate first, then manage categories, transactions, "
        "budgets, and analytics."
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(budgets_router)
app.include_router(analytics_router)


@app.get(
    "/",
    response_model=MessageResponse,
    tags=["system"],
    summary="Check that the API is running"
)
def root():
    return {"message": "Expense Tracker API is running"}


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Check API health"
)
def health_check():
    return {"status": "ok"}
