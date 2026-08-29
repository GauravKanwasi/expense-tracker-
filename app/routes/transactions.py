from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Transaction, Category, User
from ..schemas import TransactionCreate, TransactionUpdate
from ..security import get_current_user


router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)


@router.post("/")
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

    if transaction.type not in ["income", "expense"]:
        raise HTTPException(
            status_code=400,
            detail="Type must be either income or expense"
        )

    if transaction.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than 0"
        )

    new_transaction = Transaction(
        user_id=current_user.id,
        category_id=transaction.category_id,
        amount=transaction.amount,
        type=transaction.type,
        description=transaction.description,
        date=transaction.date
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return {
        "id": new_transaction.id,
        "category_id": new_transaction.category_id,
        "amount": new_transaction.amount,
        "type": new_transaction.type,
        "description": new_transaction.description,
        "date": new_transaction.date
    }


@router.get("/")
def get_transactions(
    type: str | None = None,
    category_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

    transactions = query.order_by(
        Transaction.date.desc()
    ).all()

    return [
        {
            "id": transaction.id,
            "category_id": transaction.category_id,
            "amount": transaction.amount,
            "type": transaction.type,
            "description": transaction.description,
            "date": transaction.date,
            "created_at": transaction.created_at
        }
        for transaction in transactions
    ]


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return {
        "id": transaction.id,
        "category_id": transaction.category_id,
        "amount": transaction.amount,
        "type": transaction.type,
        "description": transaction.description,
        "date": transaction.date,
        "created_at": transaction.created_at
    }


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    category = db.query(Category).filter(
        Category.id == transaction_data.category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    if transaction_data.type not in ["income", "expense"]:
        raise HTTPException(
            status_code=400,
            detail="Type must be either income or expense"
        )

    if transaction_data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than 0"
        )

    transaction.category_id = transaction_data.category_id
    transaction.amount = transaction_data.amount
    transaction.type = transaction_data.type
    transaction.description = transaction_data.description
    transaction.date = transaction_data.date

    db.commit()
    db.refresh(transaction)

    return {
        "id": transaction.id,
        "category_id": transaction.category_id,
        "amount": transaction.amount,
        "type": transaction.type,
        "description": transaction.description,
        "date": transaction.date,
        "created_at": transaction.created_at
    }


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transaction deleted successfully"
    }
