from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Budget, Transaction, User
from ..schemas import BudgetCreate, BudgetResponse, BudgetUpdate, MessageResponse
from ..security import get_current_user


router = APIRouter(
    prefix="/budgets",
    tags=["budgets"]
)

CENT = Decimal("0.01")


def money_value(value):
    # SQLite aggregates can be floats, so return a fixed two-decimal value.
    return Decimal(str(value or 0)).quantize(CENT)


def month_bounds(year: int, month: int):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end


def budget_response(db: Session, budget: Budget):
    # Spending includes expense transactions from this budget's month only.
    start, end = month_bounds(budget.year, budget.month)
    spent = db.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        Transaction.user_id == budget.user_id,
        Transaction.type == "expense",
        Transaction.date >= start,
        Transaction.date < end
    ).scalar()

    amount = money_value(budget.amount)
    spent = money_value(spent)

    return {
        "id": budget.id,
        "year": budget.year,
        "month": budget.month,
        "amount": amount,
        "spent": spent,
        "remaining": amount - spent,
        "percentage": float(min((spent / amount) * 100, Decimal("100"))),
        "created_at": budget.created_at
    }


def get_user_budget(db: Session, budget_id: int, user_id: int):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Budget not found"
        )

    return budget


@router.post(
    "/",
    response_model=BudgetResponse,
    summary="Create a monthly budget"
)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_budget = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.year == budget_data.year,
        Budget.month == budget_data.month
    ).first()

    if existing_budget:
        raise HTTPException(
            status_code=400,
            detail="A budget for this month already exists"
        )

    new_budget = Budget(
        user_id=current_user.id,
        year=budget_data.year,
        month=budget_data.month,
        amount=budget_data.amount
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return budget_response(db, new_budget)


@router.get(
    "/",
    response_model=list[BudgetResponse],
    summary="List monthly budgets"
)
def get_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).order_by(
        Budget.year.desc(),
        Budget.month.desc()
    ).all()

    return [budget_response(db, budget) for budget in budgets]


@router.get(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Get a monthly budget"
)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = get_user_budget(db, budget_id, current_user.id)

    return budget_response(db, budget)


@router.put(
    "/{budget_id}",
    response_model=BudgetResponse,
    summary="Update a monthly budget"
)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = get_user_budget(db, budget_id, current_user.id)

    duplicate_budget = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.year == budget_data.year,
        Budget.month == budget_data.month,
        Budget.id != budget_id
    ).first()

    if duplicate_budget:
        raise HTTPException(
            status_code=400,
            detail="A budget for this month already exists"
        )

    budget.year = budget_data.year
    budget.month = budget_data.month
    budget.amount = budget_data.amount

    db.commit()
    db.refresh(budget)

    return budget_response(db, budget)


@router.delete(
    "/{budget_id}",
    response_model=MessageResponse,
    summary="Delete a monthly budget"
)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = get_user_budget(db, budget_id, current_user.id)

    db.delete(budget)
    db.commit()

    return {
        "message": "Budget deleted successfully"
    }
