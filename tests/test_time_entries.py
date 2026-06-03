# tests/test_time_entries.py
from datetime import datetime, timedelta


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


def make_times(start_hour=9, duration_hours=2.0):
    """
    Generate a start_time and end_time pair as ISO strings.
    Default: 09:00 to 11:00 on a fixed date.
    Using a fixed date keeps tests deterministic — never use date.today() in tests.
    """
    base = datetime(2026, 6, 1, start_hour, 0, 0)
    end  = base + timedelta(hours=duration_hours)
    return base.isoformat(), end.isoformat()


def create_time_entry(client, auth_headers, project_id,
                      duration_hours=2.0, description="Test work"):
    """Helper to create a time entry with auto-generated start/end times."""
    start_time, end_time = make_times(duration_hours=duration_hours)
    response = client.post("/time-entries/", json={
        "project_id":  project_id,
        "start_time":  start_time,
        "end_time":    end_time,
        "description": description
    }, headers=auth_headers)
    return response.json()


def register_and_login(client, full_name, email, password):
    client.post("/auth/register", json={
        "full_name": full_name,
        "email":     email,
        "password":  password
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
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    start_time, end_time = make_times(start_hour=9, duration_hours=3.5)
    response = client.post("/time-entries/", json={
        "project_id":  project_id,
        "start_time":  start_time,
        "end_time":    end_time,
        "description": "Frontend development"
    }, headers=auth_headers)

    assert response.status_code in (200, 201)
    data = response.json()
    assert data["duration"]   == 3.5
    assert data["project_id"] == project_id
    assert "id"         in data
    assert "start_time" in data
    assert "end_time"   in data


def test_duration_calculated_automatically(client, auth_headers):
    """
    Duration is never sent by the client — it must be
    calculated by the backend from start_time and end_time.
    """
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    # Exactly 2 hours 30 minutes = 2.5h
    start_time = "2026-06-01T09:00:00"
    end_time   = "2026-06-01T11:30:00"

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "start_time": start_time,
        "end_time":   end_time,
    }, headers=auth_headers)

    assert response.status_code in (200, 201)
    assert response.json()["duration"] == 2.5


def test_create_time_entry_end_before_start_rejected(client, auth_headers):
    """
    end_time before start_time must be rejected with 422.
    This is validated by the Pydantic schema before hitting the service.
    """
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "start_time": "2026-06-01T11:00:00",
        "end_time":   "2026-06-01T09:00:00",   # end is BEFORE start
    }, headers=auth_headers)

    assert response.status_code == 422


def test_create_time_entry_end_equal_start_rejected(client, auth_headers):
    """
    end_time equal to start_time means zero duration — must be rejected.
    """
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "start_time": "2026-06-01T09:00:00",
        "end_time":   "2026-06-01T09:00:00",   # same time
    }, headers=auth_headers)

    assert response.status_code == 422


def test_create_time_entry_requires_auth(client, auth_headers):
    """Creating a time entry without a token is rejected."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    start_time, end_time = make_times()

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "start_time": start_time,
        "end_time":   end_time,
    })
    assert response.status_code == 401


def test_create_time_entry_for_other_users_project(client, auth_headers):
    """Logging time against another user's project is rejected with 404."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    start_time, end_time = make_times()
    response = client.post("/time-entries/", json={
        "project_id": project_id,   # belongs to User A
        "start_time": start_time,
        "end_time":   end_time,
    }, headers=user_b_headers)
    assert response.status_code == 404


def test_create_time_entry_missing_start_time(client, auth_headers):
    """A time entry without start_time fails validation."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "end_time":   "2026-06-01T11:00:00"
        # start_time missing
    }, headers=auth_headers)
    assert response.status_code == 422


def test_create_time_entry_missing_end_time(client, auth_headers):
    """A time entry without end_time fails validation."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "start_time": "2026-06-01T09:00:00"
        # end_time missing
    }, headers=auth_headers)
    assert response.status_code == 422


def test_create_time_entry_missing_project_id(client, auth_headers):
    """A time entry without a project_id fails validation."""
    start_time, end_time = make_times()
    response = client.post("/time-entries/", json={
        "start_time": start_time,
        "end_time":   end_time,
        # project_id missing
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
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    create_time_entry(client, auth_headers, project_id, duration_hours=1.0)
    create_time_entry(client, auth_headers, project_id, duration_hours=2.0)

    response = client.get("/time-entries/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_time_entry_by_id(client, auth_headers):
    """A user can fetch one of their own time entries by ID."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry      = create_time_entry(client, auth_headers, project_id)

    response = client.get(f"/time-entries/{entry['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == entry["id"]


def test_get_nonexistent_time_entry_returns_404(client, auth_headers):
    """Fetching a time entry ID that doesn't exist returns 404."""
    response = client.get("/time-entries/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Update ───────────────────────────────────────────────────────────────────

def test_update_time_entry_times(client, auth_headers):
    """
    Updating start_time and end_time recalculates duration automatically.
    This is the key behaviour of the refactor.
    """
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry      = create_time_entry(client, auth_headers, project_id,
                                   duration_hours=2.0)

    # Change to a 4-hour session
    response = client.patch(f"/time-entries/{entry['id']}", json={
        "start_time": "2026-06-01T08:00:00",
        "end_time":   "2026-06-01T12:00:00"
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["duration"] == 4.0


def test_update_time_entry_recalculates_duration(client, auth_headers):
    """
    Duration updates correctly when only end_time changes.
    Original: 2h. New end_time adds 30 min → 2.5h.
    """
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    # Create a 2h entry
    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "start_time": "2026-06-01T09:00:00",
        "end_time":   "2026-06-01T11:00:00",
    }, headers=auth_headers)
    entry = response.json()
    assert entry["duration"] == 2.0

    # Extend end_time by 30 minutes
    response = client.patch(f"/time-entries/{entry['id']}", json={
        "end_time": "2026-06-01T11:30:00"
    }, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["duration"] == 2.5


def test_update_time_entry_description(client, auth_headers):
    """A user can update the description without affecting duration."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry      = create_time_entry(client, auth_headers, project_id,
                                   duration_hours=2.0)

    response = client.patch(f"/time-entries/{entry['id']}", json={
        "description": "Updated description"
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["duration"]    == 2.0   # duration unchanged


def test_update_time_entry_invalid_times_rejected(client, auth_headers):
    """Updating with end_time before start_time is rejected."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry      = create_time_entry(client, auth_headers, project_id)

    response = client.patch(f"/time-entries/{entry['id']}", json={
        "start_time": "2026-06-01T11:00:00",
        "end_time":   "2026-06-01T09:00:00"   # end before start
    }, headers=auth_headers)

    assert response.status_code == 422


def test_update_nonexistent_time_entry_returns_404(client, auth_headers):
    """Updating a time entry that doesn't exist returns 404."""
    response = client.patch("/time-entries/99999", json={
        "start_time": "2026-06-01T09:00:00",
        "end_time":   "2026-06-01T11:00:00"
    }, headers=auth_headers)
    assert response.status_code == 404


# ─── Delete ───────────────────────────────────────────────────────────────────

def test_delete_time_entry(client, auth_headers):
    """A user can delete their own time entry."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry      = create_time_entry(client, auth_headers, project_id)

    response = client.delete(f"/time-entries/{entry['id']}",
                             headers=auth_headers)
    assert response.status_code in (200, 204)

    follow_up = client.get(f"/time-entries/{entry['id']}",
                           headers=auth_headers)
    assert follow_up.status_code == 404


def test_delete_nonexistent_time_entry_returns_404(client, auth_headers):
    """Deleting a time entry that doesn't exist returns 404."""
    response = client.delete("/time-entries/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Ownership security ───────────────────────────────────────────────────────

def test_user_cannot_see_other_users_time_entries(client, auth_headers):
    """User B cannot see User A's time entries."""
    client_id  = create_client(client, auth_headers)
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
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry      = create_time_entry(client, auth_headers, project_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get(f"/time-entries/{entry['id']}",
                          headers=user_b_headers)
    assert response.status_code == 404


def test_user_cannot_delete_other_users_time_entry(client, auth_headers):
    """User B cannot delete User A's time entry."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    entry      = create_time_entry(client, auth_headers, project_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.delete(f"/time-entries/{entry['id']}",
                             headers=user_b_headers)
    assert response.status_code == 404

    # Verify it still exists for User A
    response = client.get(f"/time-entries/{entry['id']}",
                          headers=auth_headers)
    assert response.status_code == 200