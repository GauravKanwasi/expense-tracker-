from datetime import datetime, timedelta, timezone
import os
from threading import Lock
from uuid import uuid4

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from .database import get_db
from .model import User


load_dotenv()

password_hasher = PasswordHash.recommended()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not set")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
revoked_tokens: dict[str, int] = {}
revoked_tokens_lock = Lock()


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )


def clear_revoked_tokens() -> None:
    with revoked_tokens_lock:
        revoked_tokens.clear()


def is_token_revoked(token_id: str) -> bool:
    now = int(datetime.now(timezone.utc).timestamp())

    with revoked_tokens_lock:
        expired = [key for key, expiry in revoked_tokens.items() if expiry <= now]
        for key in expired:
            revoked_tokens.pop(key, None)
        return token_id in revoked_tokens


def decode_access_token(token: str, check_revocation: bool = True) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        token_id = payload.get("jti")

        if payload.get("sub") is None or token_id is None:
            raise credentials_exception()

        if check_revocation and is_token_revoked(token_id):
            raise credentials_exception()

        return payload
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception()


def hash_password(password: str) -> str:
    # Passwords are stored only as secure hashes.
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "jti": uuid4().hex
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def revoke_access_token(token: str) -> None:
    payload = decode_access_token(token, check_revocation=False)
    token_id = payload["jti"]
    expiry = int(payload["exp"])

    with revoked_tokens_lock:
        revoked_tokens[token_id] = expiry


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise credentials_exception()

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception()

    return user
