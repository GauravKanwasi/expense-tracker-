from math import ceil
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..model import User
from ..schemas import MessageResponse, TokenResponse
from ..security import (
    create_access_token,
    oauth2_scheme,
    revoke_access_token,
    verify_password
)


router = APIRouter(prefix="/auth", tags=["Authentication"])
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 60
failed_login_attempts: dict[str, list[float]] = {}
login_attempts_lock = Lock()


def clear_login_attempts() -> None:
    with login_attempts_lock:
        failed_login_attempts.clear()


def login_attempt_key(request: Request, email: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{email}"


def check_login_rate_limit(key: str) -> None:
    now = monotonic()

    with login_attempts_lock:
        attempts = [
            attempt for attempt in failed_login_attempts.get(key, [])
            if now - attempt < LOGIN_WINDOW_SECONDS
        ]
        failed_login_attempts[key] = attempts

        if len(attempts) >= MAX_LOGIN_ATTEMPTS:
            retry_after = max(1, ceil(LOGIN_WINDOW_SECONDS - (now - attempts[0])))
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Try again shortly.",
                headers={"Retry-After": str(retry_after)}
            )


def record_failed_login(key: str) -> None:
    with login_attempts_lock:
        failed_login_attempts.setdefault(key, []).append(monotonic())


def clear_failed_login(key: str) -> None:
    with login_attempts_lock:
        failed_login_attempts.pop(key, None)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description=(
        "Send the registered email in the OAuth2 `username` field "
        "and the password in the `password` field."
    )
)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username.strip().casefold()
    attempt_key = login_attempt_key(request, email)
    check_login_rate_limit(attempt_key)
    existing_user = db.query(User).filter(
        func.lower(User.email) == email
    ).first()

    if not existing_user:
        record_failed_login(attempt_key)
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        form_data.password,
        existing_user.password_hash
    ):
        record_failed_login(attempt_key)
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    clear_failed_login(attempt_key)
    access_token = create_access_token(existing_user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke the current access token"
)
def logout(token: str = Depends(oauth2_scheme)):
    revoke_access_token(token)
    return {"message": "Logged out successfully"}
