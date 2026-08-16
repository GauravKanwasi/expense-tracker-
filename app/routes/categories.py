from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import Category, User
from ..schemas import CategoryCreate
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
        
        db.name(new_category)
        db.commit()
        db.refresh(new_category)
        
        
        
        return{
            "id": new_category.id,
            "name": new_category.name
        }