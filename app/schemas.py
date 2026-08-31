from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from datetime import datetime


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


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


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class CategoryResponse(BaseModel):
    id: int
    name: str


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str


class AnalyticsSummaryResponse(BaseModel):
    total_income: float
    total_expenses: float
    balance: float


class CategoryTotalResponse(BaseModel):
    category_id: int
    category_name: str
    total: float
