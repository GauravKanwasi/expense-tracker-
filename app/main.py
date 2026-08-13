from fastapi import FastAPI

app = FastAPI(title="Expense Tracker API")


@app.get("/")
def root():
    return {"message": "Expense Tracker API is running"}