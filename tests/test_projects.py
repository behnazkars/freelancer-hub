# tests/test_projects.py

# ─── Helpers ─────────────────────────────────────────────────────────────────

def create_client(client, auth_headers, name="Acme Corp"):
    """Create a client and return its ID."""
    response = client.post("/clients/", json={
        "name": name,
        "email": "acme@example.com"
    }, headers=auth_headers)
    return response.json()["id"]


def create_project(client, auth_headers, client_id, **overrides):
    """Create a project with sensible defaults."""
    payload = {
        "name": "Website Redesign",
        "description": "A test project",
        "client_id": client_id,
        "hourly_rate": 75.0,
        "budget": 5000.0,
        "status": "active",
        **overrides
    }
    return client.post("/projects/", json=payload, headers=auth_headers)


# ─── Create ───────────────────────────────────────────────────────────────────

def test_create_project_success(client, auth_headers):
    """An authenticated user can create a project linked to their client."""
    client_id = create_client(client, auth_headers)
    response = create_project(client, auth_headers, client_id)

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Website Redesign"
    assert data["client_id"] == client_id
    assert data["status"] == "active"
    assert "id" in data


def test_create_project_requires_auth(client, auth_headers):
    """Creating a project without a token is rejected."""
    client_id = create_client(client, auth_headers)
    response = client.post("/projects/", json={
        "name": "Website Redesign",
        "client_id": client_id
    })
    assert response.status_code == 401


def test_create_project_missing_name(client, auth_headers):
    """A project without a name fails validation."""
    client_id = create_client(client, auth_headers)
    response = client.post("/projects/", json={
        "client_id": client_id    # name is missing
    }, headers=auth_headers)
    assert response.status_code == 422


def test_create_project_missing_client_id(client, auth_headers):
    """A project without a client_id fails validation."""
    response = client.post("/projects/", json={
        "name": "Website Redesign"   # client_id is missing
    }, headers=auth_headers)
    assert response.status_code == 422


# ─── Read ─────────────────────────────────────────────────────────────────────

def test_list_projects_empty(client, auth_headers):
    """A new user starts with no projects."""
    response = client.get("/projects/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_projects_returns_own_projects(client, auth_headers):
    """Listed projects belong to the requesting user."""
    client_id = create_client(client, auth_headers)
    create_project(client, auth_headers, client_id, name="Project A")
    create_project(client, auth_headers, client_id, name="Project B")

    response = client.get("/projects/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [p["name"] for p in data]
    assert "Project A" in names
    assert "Project B" in names


def test_get_project_by_id(client, auth_headers):
    """A user can fetch one of their own projects by ID."""
    client_id = create_client(client, auth_headers)
    created = create_project(client, auth_headers, client_id).json()
    project_id = created["id"]

    response = client.get(f"/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == project_id


def test_get_nonexistent_project_returns_404(client, auth_headers):
    """Fetching a project ID that doesn't exist returns 404."""
    response = client.get("/projects/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Update ───────────────────────────────────────────────────────────────────

def test_update_project(client, auth_headers):
    """A user can update their own project."""
    client_id = create_client(client, auth_headers)
    created = create_project(client, auth_headers, client_id).json()
    project_id = created["id"]

    response = client.patch(f"/projects/{project_id}", json={
        "name": "Updated Project Name",
        "status": "completed"
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project Name"
    assert data["status"] == "completed"


def test_update_nonexistent_project_returns_404(client, auth_headers):
    """Updating a project that doesn't exist returns 404."""
    response = client.patch("/projects/99999", json={
        "name": "Ghost Project"
    }, headers=auth_headers)
    assert response.status_code == 404


# ─── Delete ───────────────────────────────────────────────────────────────────

def test_delete_project(client, auth_headers):
    """A user can delete their own project."""
    client_id = create_client(client, auth_headers)
    created = create_project(client, auth_headers, client_id).json()
    project_id = created["id"]

    response = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert response.status_code in (200, 204)

    # Verify it's actually gone
    follow_up = client.get(f"/projects/{project_id}", headers=auth_headers)
    assert follow_up.status_code == 404


def test_delete_nonexistent_project_returns_404(client, auth_headers):
    """Deleting a project that doesn't exist returns 404."""
    response = client.delete("/projects/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Ownership security ───────────────────────────────────────────────────────

def register_and_login(client, full_name, email, password):
    """Create a second independent user and return their auth headers."""
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


def test_user_cannot_see_other_users_projects(client, auth_headers):
    """User B cannot see User A's projects in their own list."""
    client_id = create_client(client, auth_headers)
    create_project(client, auth_headers, client_id, name="Secret Project")

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get("/projects/", headers=user_b_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_access_other_users_project_by_id(client, auth_headers):
    """User B cannot fetch User A's project directly by ID."""
    client_id = create_client(client, auth_headers)
    created = create_project(client, auth_headers, client_id).json()
    project_id = created["id"]

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get(f"/projects/{project_id}", headers=user_b_headers)
    assert response.status_code == 404


def test_user_cannot_delete_other_users_project(client, auth_headers):
    """User B cannot delete User A's project."""
    client_id = create_client(client, auth_headers)
    created = create_project(client, auth_headers, client_id).json()
    project_id = created["id"]

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.delete(f"/projects/{project_id}", headers=user_b_headers)
    assert response.status_code == 404

    # Verify it still exists for User A
    response = client.get(f"/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200