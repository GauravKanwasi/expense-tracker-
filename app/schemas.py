from enum import Enum

from pydantic import BaseModel, EmailStr, Field, model_validator

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
    debt = "debt"
    investment = "investment"


class DebtDirection(str, Enum):
    borrowed = "borrowed"
    lent = "lent"


class InvestmentAction(str, Enum):
    contribution = "contribution"
    withdrawal = "withdrawal"


class TransactionBase(BaseModel):
    category_id: int
    amount: float = Field(gt=0)
    type: TransactionType
    description: str | None = None
    date: datetime
    debt_direction: DebtDirection | None = None
    interest_amount: float | None = Field(default=None, ge=0)
    investment_action: InvestmentAction | None = None

    @model_validator(mode="after")
    def validate_type_details(self):
        if self.type == TransactionType.debt:
            if self.debt_direction is None:
                raise ValueError("debt_direction is required for debt transactions")
        elif self.debt_direction is not None or self.interest_amount is not None:
            raise ValueError("Debt details can only be used for debt transactions")

        if self.type == TransactionType.investment:
            if self.investment_action is None:
                raise ValueError("investment_action is required for investment transactions")
        elif self.investment_action is not None:
            raise ValueError("investment_action can only be used for investment transactions")

        return self


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(TransactionBase):
    pass


class TransactionResponse(BaseModel):
    id: int
    category_id: int
    amount: float
    type: TransactionType
    description: str | None = None
    date: datetime
    debt_direction: DebtDirection | None = None
    interest_amount: float | None = None
    investment_action: InvestmentAction | None = None
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
    debt_borrowed: float
    debt_lent: float
    debt_interest: float
    investment_contributions: float
    investment_withdrawals: float


class CategoryTotalResponse(BaseModel):
    category_id: int
    category_name: str
    total: float
