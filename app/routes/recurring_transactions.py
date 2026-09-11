from calendar import monthrange
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..finance import in_user_timezone, to_utc, user_zone
from ..model import Category, RecurringTransaction, Transaction, User
from ..schemas import (
    MessageResponse,
    RecurringGenerationRequest,
    RecurringGenerationResponse,
    RecurringTransactionCreate,
    RecurringTransactionResponse,
    RecurringTransactionUpdate,
)
from ..security import get_current_user
from .transactions import transaction_response

router = APIRouter(prefix="/recurring-transactions", tags=["recurring transactions"])
MAX_GENERATIONS_PER_REQUEST = 120


def recurring_response(rule: RecurringTransaction):
    return {
        "id": rule.id,
        "category_id": rule.category_id,
        "amount": rule.amount,
        "type": rule.type,
        "description": rule.description,
        "debt_direction": rule.debt_direction,
        "interest_amount": rule.interest_amount,
        "investment_action": rule.investment_action,
        "frequency": rule.frequency,
        "next_due_at": rule.next_due_at,
        "active": rule.active,
        "created_at": rule.created_at,
    }


def get_user_rule(db: Session, rule_id: int, user_id: int) -> RecurringTransaction:
    rule = (
        db.query(RecurringTransaction)
        .filter(
            RecurringTransaction.id == rule_id,
            RecurringTransaction.user_id == user_id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Recurring transaction not found")
    return rule


def verify_category(db: Session, category_id: int, user_id: int) -> None:
    if (
        not db.query(Category.id)
        .filter(
            Category.id == category_id,
            Category.user_id == user_id,
        )
        .first()
    ):
        raise HTTPException(status_code=404, detail="Category not found")


def apply_rule(rule: RecurringTransaction, data, timezone_name: str) -> None:
    zone = user_zone(timezone_name)
    due_at = to_utc(data.next_due_at, zone)
    rule.category_id = data.category_id
    rule.amount = data.amount
    rule.type = data.type.value
    rule.description = data.description
    rule.debt_direction = data.debt_direction.value if data.debt_direction else None
    rule.interest_amount = data.interest_amount
    rule.investment_action = data.investment_action.value if data.investment_action else None
    rule.frequency = data.frequency.value
    rule.due_day = in_user_timezone(due_at, zone).day
    rule.next_due_at = due_at
    rule.active = data.active


def next_due_at(rule: RecurringTransaction, timezone_name: str) -> datetime:
    zone = user_zone(timezone_name)
    local_due = in_user_timezone(rule.next_due_at, zone)
    if rule.frequency == "weekly":
        return to_utc(local_due + timedelta(days=7), zone)

    month = local_due.month % 12 + 1
    year = local_due.year + (local_due.month == 12)
    day = min(rule.due_day, monthrange(year, month)[1])
    return to_utc(local_due.replace(year=year, month=month, day=day), zone)


def has_generated_due(db: Session, rule: RecurringTransaction) -> bool:
    return (
        db.query(Transaction.id)
        .filter(
            Transaction.recurring_transaction_id == rule.id,
            Transaction.date == rule.next_due_at,
        )
        .first()
        is not None
    )


@router.post(
    "/", response_model=RecurringTransactionResponse, summary="Create a recurring transaction"
)
def create_recurring_transaction(
    rule_data: RecurringTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_category(db, rule_data.category_id, current_user.id)
    rule = RecurringTransaction(user_id=current_user.id)
    apply_rule(rule, rule_data, current_user.timezone)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return recurring_response(rule)


@router.get(
    "/", response_model=list[RecurringTransactionResponse], summary="List recurring transactions"
)
def list_recurring_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rules = (
        db.query(RecurringTransaction)
        .filter(RecurringTransaction.user_id == current_user.id)
        .order_by(RecurringTransaction.active.desc(), RecurringTransaction.next_due_at)
        .all()
    )
    return [recurring_response(rule) for rule in rules]


@router.post(
    "/generate", response_model=RecurringGenerationResponse, summary="Generate due transactions"
)
def generate_due_transactions(
    request: RecurringGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    zone = user_zone(current_user.timezone)
    through_date = request.through_date or datetime.now(zone).date()
    rules = (
        db.query(RecurringTransaction)
        .filter(
            RecurringTransaction.user_id == current_user.id,
            RecurringTransaction.active.is_(True),
        )
        .with_for_update()
        .order_by(RecurringTransaction.next_due_at)
        .all()
    )
    generated = []

    for rule in rules:
        while in_user_timezone(rule.next_due_at, zone).date() <= through_date:
            if len(generated) >= MAX_GENERATIONS_PER_REQUEST:
                db.commit()
                return {"generated": [transaction_response(item) for item in generated]}
            if not has_generated_due(db, rule):
                entry = Transaction(
                    user_id=current_user.id,
                    category_id=rule.category_id,
                    amount=rule.amount,
                    type=rule.type,
                    description=rule.description,
                    debt_direction=rule.debt_direction,
                    interest_amount=rule.interest_amount,
                    investment_action=rule.investment_action,
                    date=rule.next_due_at,
                    recurring_transaction_id=rule.id,
                )
                db.add(entry)
                db.flush()
                generated.append(entry)
            rule.next_due_at = next_due_at(rule, current_user.timezone)

    db.commit()
    for entry in generated:
        db.refresh(entry)
    return {"generated": [transaction_response(item) for item in generated]}


@router.get(
    "/{rule_id}", response_model=RecurringTransactionResponse, summary="Get a recurring transaction"
)
def get_recurring_transaction(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return recurring_response(get_user_rule(db, rule_id, current_user.id))


@router.put(
    "/{rule_id}",
    response_model=RecurringTransactionResponse,
    summary="Update a recurring transaction",
)
def update_recurring_transaction(
    rule_id: int,
    rule_data: RecurringTransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_category(db, rule_data.category_id, current_user.id)
    rule = get_user_rule(db, rule_id, current_user.id)
    apply_rule(rule, rule_data, current_user.timezone)
    db.commit()
    db.refresh(rule)
    return recurring_response(rule)


@router.delete(
    "/{rule_id}", response_model=MessageResponse, summary="Delete a recurring transaction"
)
def delete_recurring_transaction(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = get_user_rule(db, rule_id, current_user.id)
    db.delete(rule)
    db.commit()
    return {"message": "Recurring transaction deleted successfully"}
