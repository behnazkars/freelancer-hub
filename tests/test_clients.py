# tests/test_clients.py

# ─── Helpers ─────────────────────────────────────────────────────────────────

def create_client(client, auth_headers, **overrides):
    """Helper to create a client with sensible defaults."""
    payload = {
        "name": "Acme Corp",
        "email": "acme@example.com",
        "phone": "555-1234",
        "company": "Acme",
        **overrides   # lets individual tests override specific fields
    }
    return client.post("/clients/", json=payload, headers=auth_headers)


# ─── Create ───────────────────────────────────────────────────────────────────

def test_create_client_success(client, auth_headers):
    """An authenticated user can create a client."""
    response = create_client(client, auth_headers)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["email"] == "acme@example.com"
    assert "id" in data


def test_create_client_requires_auth(client):
    """Creating a client without a token is rejected."""
    response = client.post("/clients/", json={
        "name": "Acme Corp",
        "email": "acme@example.com",
    })
    assert response.status_code == 401


def test_create_client_missing_name(client, auth_headers):
    """A client without a name fails validation."""
    response = client.post("/clients/", json={
        "email": "acme@example.com"   # name is missing
    }, headers=auth_headers)
    assert response.status_code == 422


# ─── Read ─────────────────────────────────────────────────────────────────────

def test_list_clients_empty(client, auth_headers):
    """A new user starts with no clients."""
    response = client.get("/clients/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_clients_returns_own_clients(client, auth_headers):
    """Listed clients belong to the requesting user."""
    create_client(client, auth_headers, name="Client A")
    create_client(client, auth_headers, name="Client B")

    response = client.get("/clients/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [c["name"] for c in data]
    assert "Client A" in names
    assert "Client B" in names


def test_get_client_by_id(client, auth_headers):
    """A user can fetch one of their own clients by ID."""
    created = create_client(client, auth_headers).json()
    client_id = created["id"]

    response = client.get(f"/clients/{client_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == client_id


def test_get_nonexistent_client_returns_404(client, auth_headers):
    """Fetching a client ID that doesn't exist returns 404."""
    response = client.get("/clients/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Update ───────────────────────────────────────────────────────────────────

def test_update_client(client, auth_headers):
    """A user can update their own client."""
    created = create_client(client, auth_headers).json()
    client_id = created["id"]

    response = client.patch(f"/clients/{client_id}", json={
        "name": "Acme Corp Updated",
        "email": "new@acme.com",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Acme Corp Updated"


def test_update_nonexistent_client_returns_404(client, auth_headers):
    """Updating a client that doesn't exist returns 404."""
    response = client.patch("/clients/99999", json={
        "name": "Ghost"
    }, headers=auth_headers)
    assert response.status_code == 404


# ─── Delete ───────────────────────────────────────────────────────────────────

def test_delete_client(client, auth_headers):
    """A user can delete their own client."""
    created = create_client(client, auth_headers).json()
    client_id = created["id"]

    response = client.delete(f"/clients/{client_id}", headers=auth_headers)
    assert response.status_code in (200, 204)

    # Verify it's actually gone
    follow_up = client.get(f"/clients/{client_id}", headers=auth_headers)
    assert follow_up.status_code == 404


def test_delete_nonexistent_client_returns_404(client, auth_headers):
    """Deleting a client that doesn't exist returns 404."""
    response = client.delete("/clients/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Ownership security ───────────────────────────────────────────────────────

def register_and_login(client, full_name, email, password):
    """Helper to create a second independent user and return their auth headers."""
    client.post("/auth/register", json={
        "full_name": full_name,
        "email": email,
        "password": password
    })
    response = client.post("/auth/login", data={
        "username": email,
        "password": password
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_cannot_see_other_users_clients(client, auth_headers):
    """User B cannot see User A's clients in their own list."""
    # User A creates a client
    create_client(client, auth_headers, name="Secret Client")

    # User B logs in and lists their clients
    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get("/clients/", headers=user_b_headers)
    assert response.status_code == 200
    assert response.json() == []   # Bob sees nothing


def test_user_cannot_access_other_users_client_by_id(client, auth_headers):
    """User B cannot fetch User A's client directly by ID."""
    created = create_client(client, auth_headers).json()
    client_id = created["id"]

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get(f"/clients/{client_id}", headers=user_b_headers)
    assert response.status_code == 404   # looks like it doesn't exist


def test_user_cannot_delete_other_users_client(client, auth_headers):
    """User B cannot delete User A's client."""
    created = create_client(client, auth_headers).json()
    client_id = created["id"]

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.delete(f"/clients/{client_id}", headers=user_b_headers)
    assert response.status_code == 404

    # Verify it still exists for User A
    response = client.get(f"/clients/{client_id}", headers=auth_headers)
    assert response.status_code == 200