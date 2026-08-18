from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Transaction, Category, User
from ..schemas import TransactionCreate
from ..security import get_current_user


router = APIRouter(prefix="/transactions", tags=["transactions"])


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