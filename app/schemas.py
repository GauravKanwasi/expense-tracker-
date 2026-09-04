from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    PlainSerializer,
    model_validator
)

from datetime import datetime


def serialize_money(value: Decimal) -> str:
    # JSON number ko browser kabhi-kabhi round kar deta hai, isliye string bhejo.
    formatted = format(value, "f")
    return formatted if "." in formatted else formatted + ".00"


MoneyAmount = Annotated[
    Decimal,
    Field(decimal_places=2),
    PlainSerializer(
        serialize_money,
        return_type=str,
        when_used="json"
    )
]
PositiveMoney = Annotated[
    Decimal,
    Field(gt=Decimal("0"), max_digits=31, decimal_places=2)
]
NonNegativeMoney = Annotated[
    Decimal,
    Field(ge=Decimal("0"), max_digits=31, decimal_places=2)
]


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
    amount: PositiveMoney
    type: TransactionType
    description: str | None = Field(default=None, max_length=255)
    date: datetime
    debt_direction: DebtDirection | None = None
    interest_amount: NonNegativeMoney | None = None
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
    amount: MoneyAmount
    type: TransactionType
    description: str | None = None
    date: datetime
    debt_direction: DebtDirection | None = None
    interest_amount: MoneyAmount | None = None
    investment_action: InvestmentAction | None = None
    created_at: datetime | None = None


class BudgetBase(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: PositiveMoney


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BudgetBase):
    pass


class BudgetResponse(BudgetBase):
    id: int
    amount: MoneyAmount
    spent: MoneyAmount
    remaining: MoneyAmount
    percentage: float
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
    total_income: MoneyAmount
    total_expenses: MoneyAmount
    balance: MoneyAmount
    cash_balance: MoneyAmount
    budget_total: MoneyAmount
    budget_spent: MoneyAmount
    budget_remaining: MoneyAmount
    available_after_budgets: MoneyAmount
    debt_borrowed: MoneyAmount
    debt_lent: MoneyAmount
    debt_interest: MoneyAmount
    investment_contributions: MoneyAmount
    investment_withdrawals: MoneyAmount


class CategoryTotalResponse(BaseModel):
    category_id: int
    category_name: str
    total: MoneyAmount
