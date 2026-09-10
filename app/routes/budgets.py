from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..finance import ZERO, money, money_difference, money_sum, month_bounds, month_key, user_zone
from ..model import Budget, Transaction, User
from ..schemas import BudgetCreate, BudgetResponse, BudgetUpdate, MessageResponse
from ..security import get_current_user

router = APIRouter(prefix="/budgets", tags=["budgets"])


def monthly_expenses(db: Session, budgets: list[Budget], timezone_name: str):
    """Group exact expense values once, avoiding SQLite's floating-point SUM."""
    if not budgets:
        return {}

    zone = user_zone(timezone_name)
    bounds = [month_bounds(budget.year, budget.month, zone) for budget in budgets]
    expected_months = {(budget.year, budget.month) for budget in budgets}
    rows = (
        db.query(Transaction.date, Transaction.amount)
        .filter(
            Transaction.user_id == budgets[0].user_id,
            Transaction.type == "expense",
            Transaction.date >= min(start for start, _ in bounds),
            Transaction.date < max(end for _, end in bounds),
        )
        .all()
    )
    totals = {key: ZERO for key in expected_months}
    for occurred_at, amount in rows:
        key = month_key(occurred_at, zone)
        if key in totals:
            totals[key] = money_sum((totals[key], amount))
    return totals


def budget_response(budget: Budget, spent):
    amount = money(budget.amount)
    spent = money(spent)
    remaining = money_difference(amount, spent)

    return {
        "id": budget.id,
        "year": budget.year,
        "month": budget.month,
        "amount": amount,
        "spent": spent,
        "remaining": remaining,
        "percentage": float(min((spent / amount) * 100, Decimal("100"))),
        "created_at": budget.created_at,
    }


def budget_responses(db: Session, budgets: list[Budget], timezone_name: str):
    expenses = monthly_expenses(db, budgets, timezone_name)
    return [
        budget_response(budget, expenses.get((budget.year, budget.month), ZERO))
        for budget in budgets
    ]


def get_user_budget(db: Session, budget_id: int, user_id: int):
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    return budget


@router.post("/", response_model=BudgetResponse, summary="Create a monthly budget")
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.year == budget_data.year,
            Budget.month == budget_data.month,
        )
        .first()
    )

    if existing_budget:
        raise HTTPException(status_code=400, detail="A budget for this month already exists")

    new_budget = Budget(
        user_id=current_user.id,
        year=budget_data.year,
        month=budget_data.month,
        amount=budget_data.amount,
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return budget_responses(db, [new_budget], current_user.timezone)[0]


@router.get("/", response_model=list[BudgetResponse], summary="List monthly budgets")
def get_budgets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    budgets = (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id)
        .order_by(Budget.year.desc(), Budget.month.desc())
        .all()
    )

    return budget_responses(db, budgets, current_user.timezone)


@router.get("/{budget_id}", response_model=BudgetResponse, summary="Get a monthly budget")
def get_budget(
    budget_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    budget = get_user_budget(db, budget_id, current_user.id)

    return budget_responses(db, [budget], current_user.timezone)[0]


@router.put("/{budget_id}", response_model=BudgetResponse, summary="Update a monthly budget")
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = get_user_budget(db, budget_id, current_user.id)

    duplicate_budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.year == budget_data.year,
            Budget.month == budget_data.month,
            Budget.id != budget_id,
        )
        .first()
    )

    if duplicate_budget:
        raise HTTPException(status_code=400, detail="A budget for this month already exists")

    budget.year = budget_data.year
    budget.month = budget_data.month
    budget.amount = budget_data.amount

    db.commit()
    db.refresh(budget)

    return budget_responses(db, [budget], current_user.timezone)[0]


@router.delete("/{budget_id}", response_model=MessageResponse, summary="Delete a monthly budget")
def delete_budget(
    budget_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    budget = get_user_budget(db, budget_id, current_user.id)

    db.delete(budget)
    db.commit()

    return {"message": "Budget deleted successfully"}
