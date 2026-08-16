from fastapi import FastAPI

from .database import engine, Base

from .routes.categories import router as category_router

from .import model

from .routes.users import router as user_router

from .routes.auth import router as auth_router

Base.metadata.create_all(bind=engine)


app = FastAPI(title="Expense Tracker API")

app.include_router(user_router)

app.include_router(auth_router)

app.include_router(category_router)


@app.get("/")
def root():
    return {"message": "Expense Tracker API is running"}