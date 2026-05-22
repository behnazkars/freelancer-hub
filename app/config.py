# app/config.py
from pydantic_settings import BaseSettings  # reads .env automatically
from typing import Optional

class Settings(BaseSettings):
    """
    Central configuration for the app.
    In production, these are set as environment variables on Render.
    In development, they come from the .env file.
    """
    app_name: str = "Freelancer Business Hub"
    debug: bool = False  # always False in production

    # In development: sqlite:///./freelancer_hub.db
    # In production:  postgresql://... (set by Render automatically)
    database_url: str = "sqlite:///./freelancer_hub.db"

    # Security — we'll fill these in properly later
    secret_key: str = "CHANGE_THIS_BEFORE_PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Optional: for CORS if you add a separate frontend later
    allowed_origins: Optional[str] = "*"

    class Config:
        env_file = ".env"  # tells Pydantic where to find the .env file


# Create a single instance that the whole app imports
settings = Settings()