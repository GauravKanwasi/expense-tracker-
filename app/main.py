from fastapi import FastAPI

from .database import engine, Base

from .import model

from .routes.users import router as user_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API")

app.include_router(user_router)

@app.get("/")
def root():
    return {"message": "Expense Tracker API is running"}