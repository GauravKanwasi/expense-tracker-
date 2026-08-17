from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Category, User
from ..schemas import CategoryCreate, CategoryUpdate
from ..security import get_current_user


router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/")
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_category = db.query(Category).filter(
        Category.name == category.name,
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

    return {
        "id": new_category.id,
        "name": new_category.name
    }


@router.get("/")
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(Category).filter(
        Category.user_id == current_user.id
    ).all()

    return [
        {
            "id": category.id,
            "name": category.name
        }
        for category in categories
    ]


@router.get("/{category_id}")
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return {
        "id": category.id,
        "name": category.name
    }


@router.put("/{category_id}")
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    duplicate_category = db.query(Category).filter(
        Category.name == category_data.name,
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

    return {
        "id": category.id,
        "name": category.name
    }


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully"
    }