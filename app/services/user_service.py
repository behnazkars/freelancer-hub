# app/services/user_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserRegister
from app.auth.auth import hash_password, verify_password, create_access_token


def get_user_by_email(db: Session, email: str):
    """Look up a user by their email address."""
    return db.query(User).filter(User.email == email).first()


def register_user(db: Session, user_data: UserRegister) -> User:
    """
    Create a new user account.
    Raises an error if the email is already registered.
    """
    # Check if email already exists
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password — NEVER store plain text
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # reload from DB to get generated id, created_at etc.
    return new_user


def login_user(db: Session, email: str, password: str) -> str:
    """
    Verify credentials and return a JWT access token.
    We use a vague error message intentionally — never tell
    the client whether the email or password was wrong.
    That would help attackers know which emails exist.
    """
    user = get_user_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_access_token(data={"sub": user.email})
    return token