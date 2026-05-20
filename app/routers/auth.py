# app/routers/auth.py
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserRegister, UserResponse, TokenResponse
from app.services.user_service import register_user, login_user
from app.auth.auth import get_current_user
from app.models.user import User

# APIRouter is like a mini FastAPI app — it groups related routes.
# We'll attach this to the main app with a prefix.
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account."""
    return register_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
def login(
    # OAuth2PasswordRequestForm is a FastAPI built-in that
    # reads 'username' and 'password' from a form body.
    # This is the standard OAuth2 format — that's why we
    # map 'username' to our email field below.
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Log in and receive a JWT access token."""
    token = login_user(db, form_data.username, form_data.password)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the currently logged-in user's profile.
    Depends(get_current_user) protects this route —
    no valid token = 401 Unauthorized automatically.
    """
    return current_user