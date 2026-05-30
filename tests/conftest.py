# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """A user that has been registered but not logged in."""
    payload = {
        "full_name": "Test User",       # ← was "username"
        "email": "test@example.com",
        "password": "SecurePass123"
    }
    client.post("/auth/register", json=payload)
    return payload


@pytest.fixture
def auth_headers(client, registered_user):
    """JWT headers for an already-logged-in user."""
    response = client.post("/auth/login", data={
        "username": registered_user["email"],   # ← OAuth2 form field is always
        "password": registered_user["password"] #   called "username", but you
    })                                          #   pass the EMAIL as its value
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}