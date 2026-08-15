from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import User
from ..schemas import UserLogin
from ..security import verify_password


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        User.email == user_login.email
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = verify_password(
        user_login.password,
        existing_user.password_hash
    )


    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "message": "Login successful",
        "user_id": existing_user.id,
        "email": existing_user.email
    }