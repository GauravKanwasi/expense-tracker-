from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Category, Transaction, User
from ..schemas import CategoryCreate, CategoryResponse, CategoryUpdate, MessageResponse
from ..security import get_current_user


router = APIRouter(prefix="/categories", tags=["categories"])


def category_response(category: Category):
    return {
        "id": category.id,
        "name": category.name
    }


def get_user_category(db: Session, category_id: int, user_id: int):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return category


@router.post(
    "/",
    response_model=CategoryResponse,
    summary="Create a category"
)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_category = db.query(Category).filter(
        func.lower(Category.name) == category.name.lower(),
        Category.user_id == current_user.id
    ).first()

    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists."
        )

    new_category = Category(
        name=category.name,
        user_id=current_user.id
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return category_response(new_category)


@router.get(
    "/",
    response_model=list[CategoryResponse],
    summary="List the user's categories"
)
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(Category).filter(
        Category.user_id == current_user.id
    ).all()

    return [category_response(category) for category in categories]


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category"
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = get_user_category(db, category_id, current_user.id)
    return category_response(category)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category"
)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = get_user_category(db, category_id, current_user.id)

    duplicate_category = db.query(Category).filter(
        func.lower(Category.name) == category_data.name.lower(),
        Category.user_id == current_user.id,
        Category.id != category_id
    ).first()

    if duplicate_category:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists."
        )

    category.name = category_data.name

    db.commit()
    db.refresh(category)

    return category_response(category)


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    summary="Delete a category"
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = get_user_category(db, category_id, current_user.id)

    transactions_using_category = db.query(Transaction).filter(
        Transaction.category_id == category_id,
        Transaction.user_id == current_user.id
    ).first()

    if transactions_using_category:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a category that has transactions"
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully"
    }
