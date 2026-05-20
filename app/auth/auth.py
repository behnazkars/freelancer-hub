# app/auth/auth.py
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

# CryptContext tells passlib which hashing algorithm to use.
# bcrypt is the industry standard for passwords —
# it's intentionally slow to make brute-force attacks hard.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This tells FastAPI where clients send their token.
# When FastAPI sees a request, it looks for a Bearer token
# at the /auth/login endpoint path.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ─── Password utilities ───────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Convert a plain text password into a bcrypt hash."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches the stored hash.
    Never compare passwords directly — always use this.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT token utilities ──────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT token.

    The token contains:
    - 'sub': the subject (user's email) — standard JWT field
    - 'exp': expiry timestamp — token is rejected after this

    The token is SIGNED with our SECRET_KEY so we can verify
    it wasn't tampered with. But it's NOT encrypted —
    never put sensitive data (passwords etc.) inside a JWT.
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode a JWT token and return the user's email (subject).
    Returns None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        email: str = payload.get("sub")
        return email
    except JWTError:
        return None


# ─── FastAPI dependency ───────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    This is a FastAPI dependency — add it to any route
    that requires the user to be logged in.

    FastAPI automatically:
    1. Extracts the Bearer token from the request header
    2. Calls this function
    3. Injects the returned User object into the route

    If anything fails, it raises a 401 Unauthorized error.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    # Import here to avoid circular imports
    from app.models.user import User
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user