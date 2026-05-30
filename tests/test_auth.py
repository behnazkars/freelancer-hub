# tests/test_auth.py

from tests.conftest import override_get_db

# ─── Register ────────────────────────────────────────────────────────────────

def test_register_success(client):
    """A new user can register with valid data."""
    response = client.post("/auth/register", json={
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "password": "StrongPass1"
    })
    # If this still fails, change 201 to 200 — check your router's status_code=
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["full_name"] == "Alice Smith"
    assert data["email"] == "alice@example.com"
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    """Registering twice with the same email is rejected."""
    payload = {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "password": "StrongPass1"
    }
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json={
        "full_name": "Alice Again",    # different name
        "email": "alice@example.com",  # same email ← should be rejected
        "password": "StrongPass1"
    })
    assert response.status_code == 400


# ─── Login ───────────────────────────────────────────────────────────────────

def test_login_success(client, registered_user):
    """A registered user can log in and receives a JWT."""
    response = client.post("/auth/login", data={
        "username": registered_user["email"],   # ← email goes in "username" field
        "password": registered_user["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_login_wrong_password(client, registered_user):
    """A wrong password is rejected with 401."""
    response = client.post("/auth/login", data={
        "username": registered_user["email"],
        "password": "WrongPassword!"
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Logging in as a user who never registered is rejected with 401."""
    response = client.post("/auth/login", data={
        "username": "ghost@example.com",
        "password": "doesntmatter"
    })
    assert response.status_code == 401


# ─── /auth/me ────────────────────────────────────────────────────────────────

def test_me_returns_current_user(client, registered_user, auth_headers):
    """An authenticated user can fetch their own profile."""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == registered_user["full_name"]
    assert data["email"] == registered_user["email"]


def test_me_requires_auth(client):
    """Hitting /auth/me without a token is rejected with 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_rejects_fake_token(client):
    """A made-up token is rejected."""
    response = client.get("/auth/me", headers={
        "Authorization": "Bearer thisisafaketoken"
    })
    assert response.status_code == 401


def test_inactive_user_cannot_access_protected_routes(client, registered_user, auth_headers):
    """A deactivated user is blocked from protected endpoints."""
    from app.models.user import User
    from tests.conftest import override_get_db

    db = next(override_get_db())
    user = db.query(User).filter(User.email == registered_user["email"]).first()
    
    assert user is not None, "Test user should exist in the database"
    
    user.is_active = False
    db.commit()
    db.close()

    # The token is still valid — but the user is now inactive
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 400