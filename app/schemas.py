from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class TransactionCreate(BaseModel):
    category_id: int
    amount: float = Field(gt=0)
    type: TransactionType
    description: str | None = None
    date: datetime


class TransactionUpdate(BaseModel):
    category_id: int
    amount: float = Field(gt=0)
    type: TransactionType
    description: str | None = None
    date: datetime


class TransactionResponse(BaseModel):
    id: int
    category_id: int
    amount: float
    type: TransactionType
    description: str | None = None
    date: datetime
    created_at: datetime | None = None


class BudgetBase(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: float = Field(gt=0)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BudgetBase):
    pass


class BudgetResponse(BudgetBase):
    id: int
    created_at: datetime | None = None
