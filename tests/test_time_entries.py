# tests/test_time_entries.py
from datetime import date


# ─── Helpers ─────────────────────────────────────────────────────────────────

def create_client(client, auth_headers, name="Acme Corp"):
    response = client.post("/clients/", json={
        "name": name,
        "email": "acme@example.com"
    }, headers=auth_headers)
    return response.json()["id"]


def create_project(client, auth_headers, client_id, name="Test Project"):
    response = client.post("/projects/", json={
        "name": name,
        "client_id": client_id,
        "hourly_rate": 75.0,
        "status": "active"
    }, headers=auth_headers)
    return response.json()["id"]


def create_time_entry(client, auth_headers, project_id,
                      hours=2.0, description="Test work"):
    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "hours": hours,
        "description": description,
        "date": str(date.today())
    }, headers=auth_headers)
    return response.json()


def register_and_login(client, full_name, email, password):
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


# ─── Create ───────────────────────────────────────────────────────────────────

def test_create_time_entry_success(client, auth_headers):
    """An authenticated user can log a time entry for their own project."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "hours": 3.5,
        "description": "Frontend development",
        "date": str(date.today())
    }, headers=auth_headers)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["hours"] == 3.5
    assert data["project_id"] == project_id
    assert "id" in data


def test_create_time_entry_requires_auth(client, auth_headers):
    """Creating a time entry without a token is rejected."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "hours": 2.0,
        "date": str(date.today())
    })
    assert response.status_code == 401


def test_create_time_entry_for_other_users_project(client, auth_headers):
    """Logging time against another user's project is rejected with 404."""
    # User A creates a project
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    # User B tries to log time against User A's project
    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.post("/time-entries/", json={
        "project_id": project_id,   # belongs to User A
        "hours": 2.0,
        "date": str(date.today())
    }, headers=user_b_headers)
    assert response.status_code == 404


def test_create_time_entry_missing_hours(client, auth_headers):
    """A time entry without hours fails validation."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "date": str(date.today())
        # hours is missing
    }, headers=auth_headers)
    assert response.status_code == 422


def test_create_time_entry_missing_project_id(client, auth_headers):
    """A time entry without a project_id fails validation."""
    response = client.post("/time-entries/", json={
        "hours": 2.0,
        "date": str(date.today())
        # project_id is missing
    }, headers=auth_headers)
    assert response.status_code == 422


# ─── Read ─────────────────────────────────────────────────────────────────────

def test_list_time_entries_empty(client, auth_headers):
    """A new user starts with no time entries."""
    response = client.get("/time-entries/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_time_entries_returns_own_entries(client, auth_headers):
    """Listed time entries belong to the requesting user."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    create_time_entry(client, auth_headers, project_id, hours=1.0)
    create_time_entry(client, auth_headers, project_id, hours=2.0)

    response = client.get("/time-entries/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_time_entry_by_id(client, auth_headers):
    """A user can fetch one of their own time entries by ID."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry = create_time_entry(client, auth_headers, project_id)

    response = client.get(f"/time-entries/{entry['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == entry["id"]


def test_get_nonexistent_time_entry_returns_404(client, auth_headers):
    """Fetching a time entry ID that doesn't exist returns 404."""
    response = client.get("/time-entries/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Update ───────────────────────────────────────────────────────────────────

def test_update_time_entry_hours(client, auth_headers):
    """A user can update the hours on their time entry."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry = create_time_entry(client, auth_headers, project_id, hours=2.0)

    response = client.patch(f"/time-entries/{entry['id']}", json={
        "hours": 4.5
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["hours"] == 4.5


def test_update_time_entry_description(client, auth_headers):
    """A user can update the description on their time entry."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry = create_time_entry(client, auth_headers, project_id)

    response = client.patch(f"/time-entries/{entry['id']}", json={
        "description": "Updated description"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


def test_update_nonexistent_time_entry_returns_404(client, auth_headers):
    """Updating a time entry that doesn't exist returns 404."""
    response = client.patch("/time-entries/99999", json={
        "hours": 1.0
    }, headers=auth_headers)
    assert response.status_code == 404


# ─── Delete ───────────────────────────────────────────────────────────────────

def test_delete_time_entry(client, auth_headers):
    """A user can delete their own time entry."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry = create_time_entry(client, auth_headers, project_id)

    response = client.delete(f"/time-entries/{entry['id']}", headers=auth_headers)
    assert response.status_code in (200, 204)

    follow_up = client.get(f"/time-entries/{entry['id']}", headers=auth_headers)
    assert follow_up.status_code == 404


def test_delete_nonexistent_time_entry_returns_404(client, auth_headers):
    """Deleting a time entry that doesn't exist returns 404."""
    response = client.delete("/time-entries/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Ownership security ───────────────────────────────────────────────────────

def test_user_cannot_see_other_users_time_entries(client, auth_headers):
    """User B cannot see User A's time entries."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    create_time_entry(client, auth_headers, project_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get("/time-entries/", headers=user_b_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_access_other_users_time_entry_by_id(client, auth_headers):
    """User B cannot fetch User A's time entry directly by ID."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry = create_time_entry(client, auth_headers, project_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get(f"/time-entries/{entry['id']}", headers=user_b_headers)
    assert response.status_code == 404


def test_user_cannot_delete_other_users_time_entry(client, auth_headers):
    """User B cannot delete User A's time entry."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry = create_time_entry(client, auth_headers, project_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.delete(f"/time-entries/{entry['id']}", headers=user_b_headers)
    assert response.status_code == 404

    # Verify it still exists for User A
    response = client.get(f"/time-entries/{entry['id']}", headers=auth_headers)
    assert response.status_code == 200


def test_update_time_entry_date(client, auth_headers):
    """A user can update the date on their time entry."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry = create_time_entry(client, auth_headers, project_id)

    response = client.patch(f"/time-entries/{entry['id']}", json={
        "date": "2025-01-15"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["date"] == "2025-01-15"