from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..model import User
from ..schemas import UserCreate
from ..security import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")

def create_user(user: UserCreate, db: Session = Depends(get_db)):
    
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    
    
    
    
    
    
    hashed_password = hash_password(user.password)
    new_user = User(
        name= user.name,
        email= user.email,
        password_hash= hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }