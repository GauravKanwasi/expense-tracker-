from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Budget, User
from ..schemas import BudgetCreate, BudgetResponse, BudgetUpdate
from ..security import get_current_user


router = APIRouter(
    prefix="/budgets",
    tags=["budgets"]
)


def budget_response(budget: Budget):
    return {
        "id": budget.id,
        "year": budget.year,
        "month": budget.month,
        "amount": budget.amount,
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


@router.post("/", response_model=BudgetResponse)
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

    return budget_response(new_budget)


@router.get("/", response_model=list[BudgetResponse])
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

    return [budget_response(budget) for budget in budgets]


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    budget = get_user_budget(db, budget_id, current_user.id)

    return budget_response(budget)


@router.put("/{budget_id}", response_model=BudgetResponse)
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

    return budget_response(budget)


@router.delete("/{budget_id}")
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
