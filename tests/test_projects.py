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


# ─── Scope Creep Detector ─────────────────────────────────────────────────────

from datetime import datetime, timedelta


def make_times(start_hour=9, duration_hours=2.0):
    """Generate fixed ISO start/end times. Never use date.today() in tests."""
    base = datetime(2026, 6, 1, start_hour, 0, 0)
    end  = base + timedelta(hours=duration_hours)
    return base.isoformat(), end.isoformat()


def log_hours(client, auth_headers, project_id,
              duration_hours=2.0, start_hour=9):
    """Create a time entry for a project and return the response."""
    start_time, end_time = make_times(start_hour=start_hour,
                                      duration_hours=duration_hours)
    return client.post("/time-entries/", json={
        "project_id":  project_id,
        "start_time":  start_time,
        "end_time":    end_time,
        "description": "Test work"
    }, headers=auth_headers)


def test_scope_status_no_budget_hours_set(client, auth_headers):
    """A project with no budget_hours returns alert_level 'none' — graceful no-op."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        hourly_rate=100.0
        # budget_hours intentionally omitted
    ).json()["id"]

    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alert_level"]        == "none"
    assert data["budget_hours"]       is None
    assert data["logged_hours"]       is None
    assert data["budget_used_percent"] is None


def test_scope_status_zero_budget_hours(client, auth_headers):
    """A project with budget_hours=0 returns alert_level 'none' — division by zero guard."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        hourly_rate=100.0,
        budget_hours=0.0
    ).json()["id"]

    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["alert_level"] == "none"


def test_scope_status_well_under_budget(client, auth_headers):
    """Logging 2h against a 10h budget (20%) returns alert_level 'none'."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        hourly_rate=100.0,
        budget_hours=10.0
    ).json()["id"]

    log_hours(client, auth_headers, project_id, duration_hours=2.0)

    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alert_level"]         == "none"
    assert data["logged_hours"]        == 2.0
    assert data["budget_used_percent"] == 20.0


def test_scope_status_warning_threshold(client, auth_headers):
    """Logging 8h against a 10h budget (80%) returns alert_level 'warning'."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        hourly_rate=100.0,
        budget_hours=10.0
    ).json()["id"]

    # Log 8 hours in two entries to test accumulation
    log_hours(client, auth_headers, project_id,
              duration_hours=4.0, start_hour=9)
    log_hours(client, auth_headers, project_id,
              duration_hours=4.0, start_hour=14)

    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alert_level"]         == "warning"
    assert data["logged_hours"]        == 8.0
    assert data["budget_used_percent"] == 80.0


def test_scope_status_danger_threshold(client, auth_headers):
    """Logging 10h against a 10h budget (100%) returns alert_level 'danger'."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        hourly_rate=100.0,
        budget_hours=10.0
    ).json()["id"]

    log_hours(client, auth_headers, project_id, duration_hours=10.0)

    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alert_level"]         == "danger"
    assert data["logged_hours"]        == 10.0
    assert data["budget_used_percent"] == 100.0


def test_scope_status_exceeded_budget(client, auth_headers):
    """Logging 12h against a 10h budget (120%) returns alert_level 'danger'."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        hourly_rate=100.0,
        budget_hours=10.0
    ).json()["id"]

    log_hours(client, auth_headers, project_id, duration_hours=12.0)

    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alert_level"]         == "danger"
    assert data["budget_used_percent"] == 120.0


def test_scope_status_profitability_calculations(client, auth_headers):
    """Profit margin is calculated server-side from budget_hours and hourly_rate."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        hourly_rate=100.0,
        budget_hours=10.0   # projected_revenue = 10 * 100 = $1000
    ).json()["id"]

    log_hours(client, auth_headers, project_id,
              duration_hours=5.0)   # actual_cost = 5 * 100 = $500

    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["projected_revenue"] == 1000.0
    assert data["actual_cost"]       == 500.0
    assert data["profit_margin"]     == 50.0   # (1000-500)/1000 * 100


def test_scope_status_no_time_logged(client, auth_headers):
    """A project with budget_hours but no time entries shows 0% used, no alert."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        hourly_rate=100.0,
        budget_hours=10.0
    ).json()["id"]

    # No time entries logged

    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["alert_level"]         == "none"
    assert data["logged_hours"]        == 0.0
    assert data["budget_used_percent"] == 0.0


def test_scope_status_requires_auth(client, auth_headers):
    """Fetching scope status without a token is rejected."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        budget_hours=10.0
    ).json()["id"]

    response = client.get(f"/projects/{project_id}/scope-status")
    assert response.status_code == 401


def test_scope_status_ownership_security(client, auth_headers):
    """User B cannot fetch scope status for User A's project."""
    client_id  = create_client(client, auth_headers)
    project_id = create_project(
        client, auth_headers, client_id,
        budget_hours=10.0
    ).json()["id"]

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get(
        f"/projects/{project_id}/scope-status",
        headers=user_b_headers
    )
    assert response.status_code == 404