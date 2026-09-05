from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Transaction, Category, User
from ..schemas import (
    MessageResponse,
    TransactionCreate,
    TransactionPageResponse,
    TransactionResponse,
    TransactionUpdate
)
from ..security import get_current_user


router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)


def transaction_response(transaction: Transaction):
    # Keep create, list, get, and update responses consistent.
    return {
        "id": transaction.id,
        "category_id": transaction.category_id,
        "amount": transaction.amount,
        "type": transaction.type,
        "description": transaction.description,
        "debt_direction": transaction.debt_direction,
        "interest_amount": transaction.interest_amount,
        "investment_action": transaction.investment_action,
        "date": transaction.date,
        "created_at": transaction.created_at
    }


def get_user_transaction(db: Session, transaction_id: int, user_id: int):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction


@router.post(
    "/",
    response_model=TransactionResponse,
    summary="Create a transaction"
)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(
        Category.id == transaction.category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    new_transaction = Transaction(
        user_id=current_user.id,
        category_id=transaction.category_id,
        amount=transaction.amount,
        type=transaction.type.value,
        description=transaction.description,
        debt_direction=transaction.debt_direction.value if transaction.debt_direction else None,
        interest_amount=transaction.interest_amount,
        investment_action=transaction.investment_action.value if transaction.investment_action else None,
        date=transaction.date
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return transaction_response(new_transaction)


@router.get(
    "/",
    response_model=TransactionPageResponse,
    summary="List transactions"
)
def get_transactions(
    type: str | None = Query(
        default=None,
        description="Optional filter: income, expense, debt, or investment."
    ),
    category_id: int | None = Query(
        default=None,
        gt=0,
        description="Optional category ID filter."
    ),
    start_date: date | None = Query(
        default=None,
        description="Include transactions from this date."
    ),
    end_date: date | None = Query(
        default=None,
        description="Include transactions through this date."
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of transactions to skip."
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of transactions to return."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before or equal to end_date"
            )

    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    )

    if type is not None:
        if type not in ["income", "expense", "debt", "investment"]:
            raise HTTPException(
                status_code=400,
                detail="Type must be income, expense, debt, or investment"
            )

        query = query.filter(
            Transaction.type == type
        )

    if category_id is not None:
        query = query.filter(
            Transaction.category_id == category_id
        )

    if start_date is not None:
        start_datetime = datetime.combine(
            start_date,
            time.min
        )
        query = query.filter(
            Transaction.date >= start_datetime
        )

    if end_date is not None:
        next_day = end_date + timedelta(days=1)
        end_datetime = datetime.combine(
            next_day,
            time.min
        )
        query = query.filter(
            Transaction.date < end_datetime
        )

    total = query.count()
    transactions = query.order_by(
        Transaction.date.desc(),
        Transaction.id.desc()
    ).offset(skip).limit(limit).all()

    return {
        "items": [transaction_response(item) for item in transactions],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get a transaction"
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = get_user_transaction(db, transaction_id, current_user.id)

    return transaction_response(transaction)


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update a transaction"
)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = get_user_transaction(db, transaction_id, current_user.id)

    category = db.query(Category).filter(
        Category.id == transaction_data.category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    transaction.category_id = transaction_data.category_id
    transaction.amount = transaction_data.amount
    transaction.type = transaction_data.type.value
    transaction.description = transaction_data.description
    transaction.debt_direction = transaction_data.debt_direction.value if transaction_data.debt_direction else None
    transaction.interest_amount = transaction_data.interest_amount
    transaction.investment_action = transaction_data.investment_action.value if transaction_data.investment_action else None
    transaction.date = transaction_data.date

    db.commit()
    db.refresh(transaction)

    return transaction_response(transaction)


@router.delete(
    "/{transaction_id}",
    response_model=MessageResponse,
    summary="Delete a transaction"
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = get_user_transaction(db, transaction_id, current_user.id)

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted successfully"
    }
