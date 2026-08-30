from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Transaction, Category, User
from ..schemas import TransactionCreate, TransactionResponse, TransactionUpdate
from ..security import get_current_user


router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)


def transaction_response(transaction: Transaction):
    return {
        "id": transaction.id,
        "category_id": transaction.category_id,
        "amount": transaction.amount,
        "type": transaction.type,
        "description": transaction.description,
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


@router.post("/", response_model=TransactionResponse)
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
        date=transaction.date
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return transaction_response(new_transaction)


@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    type: str | None = None,
    category_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before or equal to end_date"
            )

    if skip < 0:
        raise HTTPException(
            status_code=400,
            detail="skip cannot be negative"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100"
        )

    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    )

    if type is not None:
        if type not in ["income", "expense"]:
            raise HTTPException(
                status_code=400,
                detail="Type must be either income or expense"
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

    transactions = query.order_by(
        Transaction.date.desc()
    ).offset(skip).limit(limit).all()

    return [transaction_response(item) for item in transactions]


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = get_user_transaction(db, transaction_id, current_user.id)

    return transaction_response(transaction)


@router.put("/{transaction_id}", response_model=TransactionResponse)
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
    transaction.date = transaction_data.date

    db.commit()
    db.refresh(transaction)

    return transaction_response(transaction)


@router.delete("/{transaction_id}")
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
