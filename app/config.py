# app/config.py
from pydantic_settings import BaseSettings  # reads .env automatically


class Settings(BaseSettings):
    """
    Central configuration for the app.
    Reads from environment variables or the .env file.
    Using a class (not plain variables) lets us validate types automatically.
    """
    app_name: str = "Freelancer Business Hub"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./freelancer_hub.db"

    # Security — we'll fill these in properly later
    secret_key: str = "CHANGE_THIS_BEFORE_PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"  # tells Pydantic where to find the .env file


# Create a single instance that the whole app imports
settings = Settings()