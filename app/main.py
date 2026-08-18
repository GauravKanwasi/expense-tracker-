from fastapi import FastAPI

from .database import Base, engine
from . import model
from .routes.users import router as users_router
from .routes.auth import router as auth_router
from .routes.categories import router as categories_router
from .routes.transactions import router as transactions_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API")

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(transactions_router)


@app.get("/")
def root():
    return {"message": "Expense Tracker API is running"}