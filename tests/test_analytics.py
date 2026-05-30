# tests/test_analytics.py
from datetime import date


# ─── Helpers ─────────────────────────────────────────────────────────────────

def create_client(client, auth_headers, name="Acme Corp"):
    """Create a client and return its ID."""
    response = client.post("/clients/", json={
        "name": name,
        "email": "acme@example.com"
    }, headers=auth_headers)
    return response.json()["id"]


def create_project(client, auth_headers, client_id, name="Test Project", status="active"):
    """Create a project and return its ID."""
    response = client.post("/projects/", json={
        "name": name,
        "client_id": client_id,
        "hourly_rate": 75.0,
        "status": status
    }, headers=auth_headers)
    return response.json()["id"]


def create_invoice(client, auth_headers, client_id, amount, status="draft",
                   invoice_number="INV-001", tax_rate=0.0):
    """Create an invoice and return the full response dict."""
    response = client.post("/invoices/", json={
        "client_id": client_id,
        "invoice_number": invoice_number,
        "amount": amount,
        "tax_rate": tax_rate,
        "issue_date": str(date.today()),
        "due_date": str(date.today()),
    }, headers=auth_headers)
    data = response.json()

    # If a non-draft status is requested, update it
    if status != "draft":
        client.patch(f"/invoices/{data['id']}", json={
            "status": status
        }, headers=auth_headers)

    return data


def create_time_entry(client, auth_headers, project_id, hours):
    """Create a time entry and return the full response dict."""
    response = client.post("/time-entries/", json={
        "project_id": project_id,
        "hours": hours,
        "description": "Test work",
        "date": str(date.today())
    }, headers=auth_headers)
    return response.json()


def register_and_login(client, full_name, email, password):
    """Create an independent user and return their auth headers."""
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


# ─── Auth ─────────────────────────────────────────────────────────────────────

def test_dashboard_requires_auth(client):
    """Hitting the dashboard without a token is rejected."""
    response = client.get("/analytics/dashboard")
    assert response.status_code == 401


# ─── Empty state ──────────────────────────────────────────────────────────────

def test_dashboard_empty_state(client, auth_headers):
    """A brand new user sees all zeros — no crashes on empty data."""
    response = client.get("/analytics/dashboard", headers=auth_headers)
    assert response.status_code == 200
    kpis = response.json()["kpis"]
    assert kpis["total_revenue"] == 0.0
    assert kpis["unpaid_amount"] == 0.0
    assert kpis["active_projects"] == 0
    assert kpis["total_clients"] == 0
    assert kpis["total_hours"] == 0.0
    assert kpis["overdue_invoices"] == 0


# ─── KPI: clients and projects ────────────────────────────────────────────────

def test_dashboard_counts_total_clients(client, auth_headers):
    """total_clients reflects every client the user has created."""
    create_client(client, auth_headers, name="Client A")
    create_client(client, auth_headers, name="Client B")
    create_client(client, auth_headers, name="Client C")

    kpis = client.get("/analytics/dashboard", headers=auth_headers).json()["kpis"]
    assert kpis["total_clients"] == 3


def test_dashboard_counts_active_projects_only(client, auth_headers):
    """active_projects counts active status only — not completed ones."""
    client_id = create_client(client, auth_headers)
    create_project(client, auth_headers, client_id, name="Active 1", status="active")
    create_project(client, auth_headers, client_id, name="Active 2", status="active")
    create_project(client, auth_headers, client_id, name="Done",     status="completed")

    kpis = client.get("/analytics/dashboard", headers=auth_headers).json()["kpis"]
    assert kpis["active_projects"] == 2   # completed project is excluded


# ─── KPI: revenue ─────────────────────────────────────────────────────────────

def test_dashboard_total_revenue_counts_paid_only(client, auth_headers):
    """total_revenue only sums paid invoices — not draft, sent, or overdue."""
    client_id = create_client(client, auth_headers)

    create_invoice(client, auth_headers, client_id, amount=1000.0,
                   status="paid",    invoice_number="INV-001")
    create_invoice(client, auth_headers, client_id, amount=500.0,
                   status="paid",    invoice_number="INV-002")
    create_invoice(client, auth_headers, client_id, amount=250.0,
                   status="sent",    invoice_number="INV-003")  # not counted
    create_invoice(client, auth_headers, client_id, amount=100.0,
                   status="draft",   invoice_number="INV-004")  # not counted

    kpis = client.get("/analytics/dashboard", headers=auth_headers).json()["kpis"]
    assert kpis["total_revenue"] == 1500.0   # 1000 + 500 only


def test_dashboard_total_revenue_with_tax(client, auth_headers):
    """total_revenue uses total_amount (amount + tax), not just amount."""
    client_id = create_client(client, auth_headers)

    # amount=1000, tax_rate=10% → total_amount should be 1100
    create_invoice(client, auth_headers, client_id, amount=1000.0,
                   tax_rate=10.0, status="paid", invoice_number="INV-001")

    kpis = client.get("/analytics/dashboard", headers=auth_headers).json()["kpis"]
    # If this fails with 1000.0, your invoice service isn't adding tax to total_amount
    assert kpis["total_revenue"] == 1100.0


def test_dashboard_unpaid_amount_counts_sent_and_overdue(client, auth_headers):
    """unpaid_amount sums sent + overdue invoices only."""
    client_id = create_client(client, auth_headers)

    create_invoice(client, auth_headers, client_id, amount=800.0,
                   status="sent",    invoice_number="INV-001")
    create_invoice(client, auth_headers, client_id, amount=200.0,
                   status="overdue", invoice_number="INV-002")
    create_invoice(client, auth_headers, client_id, amount=999.0,
                   status="paid",    invoice_number="INV-003")  # not counted
    create_invoice(client, auth_headers, client_id, amount=999.0,
                   status="draft",   invoice_number="INV-004")  # not counted

    kpis = client.get("/analytics/dashboard", headers=auth_headers).json()["kpis"]
    assert kpis["unpaid_amount"] == 1000.0   # 800 + 200 only


def test_dashboard_overdue_invoices_count(client, auth_headers):
    """overdue_invoices counts only overdue-status invoices."""
    client_id = create_client(client, auth_headers)

    create_invoice(client, auth_headers, client_id, amount=100.0,
                   status="overdue", invoice_number="INV-001")
    create_invoice(client, auth_headers, client_id, amount=100.0,
                   status="overdue", invoice_number="INV-002")
    create_invoice(client, auth_headers, client_id, amount=100.0,
                   status="sent",    invoice_number="INV-003")  # not counted

    kpis = client.get("/analytics/dashboard", headers=auth_headers).json()["kpis"]
    assert kpis["overdue_invoices"] == 2


# ─── KPI: hours ───────────────────────────────────────────────────────────────

def test_dashboard_total_hours(client, auth_headers):
    """total_hours sums all time entries regardless of project."""
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)

    create_time_entry(client, auth_headers, project_id, hours=3.0)
    create_time_entry(client, auth_headers, project_id, hours=2.5)
    create_time_entry(client, auth_headers, project_id, hours=1.0)

    kpis = client.get("/analytics/dashboard", headers=auth_headers).json()["kpis"]
    assert kpis["total_hours"] == 6.5


# ─── Revenue by client ────────────────────────────────────────────────────────

def test_dashboard_revenue_by_client(client, auth_headers):
    """revenue_by_client ranks clients by paid invoice total, highest first."""
    client_a_id = create_client(client, auth_headers, name="Big Client")
    client_b_id = create_client(client, auth_headers, name="Small Client")

    create_invoice(client, auth_headers, client_a_id, amount=3000.0,
                   status="paid", invoice_number="INV-001")
    create_invoice(client, auth_headers, client_b_id, amount=500.0,
                   status="paid", invoice_number="INV-002")

    data = client.get("/analytics/dashboard", headers=auth_headers).json()
    revenue = data["revenue_by_client"]

    assert len(revenue) == 2
    assert revenue[0]["name"] == "Big Client"    # highest first
    assert revenue[0]["total"] == 3000.0
    assert revenue[1]["name"] == "Small Client"
    assert revenue[1]["total"] == 500.0


def test_dashboard_revenue_by_client_excludes_unpaid(client, auth_headers):
    """revenue_by_client only counts paid invoices."""
    client_id = create_client(client, auth_headers, name="Acme")

    create_invoice(client, auth_headers, client_id, amount=1000.0,
                   status="paid",  invoice_number="INV-001")
    create_invoice(client, auth_headers, client_id, amount=9999.0,
                   status="draft", invoice_number="INV-002")  # not counted

    data = client.get("/analytics/dashboard", headers=auth_headers).json()
    revenue = data["revenue_by_client"]

    assert len(revenue) == 1
    assert revenue[0]["total"] == 1000.0   # draft invoice ignored


# ─── Hours by project ─────────────────────────────────────────────────────────

def test_dashboard_hours_by_project(client, auth_headers):
    """hours_by_project ranks projects by total hours, highest first."""
    client_id = create_client(client, auth_headers)
    project_a = create_project(client, auth_headers, client_id, name="Big Project")
    project_b = create_project(client, auth_headers, client_id, name="Small Project")

    create_time_entry(client, auth_headers, project_a, hours=10.0)
    create_time_entry(client, auth_headers, project_b, hours=2.0)

    data = client.get("/analytics/dashboard", headers=auth_headers).json()
    hours = data["hours_by_project"]

    assert len(hours) == 2
    assert hours[0]["name"] == "Big Project"    # highest first
    assert hours[0]["total"] == 10.0
    assert hours[1]["name"] == "Small Project"
    assert hours[1]["total"] == 2.0


# ─── Recent invoices ──────────────────────────────────────────────────────────

def test_dashboard_recent_invoices_returns_last_5(client, auth_headers):
    """recent_invoices returns at most 5 invoices, newest first."""
    client_id = create_client(client, auth_headers)

    for i in range(1, 8):   # create 7 invoices
        create_invoice(client, auth_headers, client_id,
                       amount=100.0, invoice_number=f"INV-00{i}")

    data = client.get("/analytics/dashboard", headers=auth_headers).json()
    recent = data["recent_invoices"]

    assert len(recent) == 5   # capped at 5


def test_dashboard_recent_invoices_have_required_fields(client, auth_headers):
    """Each invoice in recent_invoices has the fields the frontend needs."""
    client_id = create_client(client, auth_headers)
    create_invoice(client, auth_headers, client_id,
                   amount=500.0, invoice_number="INV-001")

    data = client.get("/analytics/dashboard", headers=auth_headers).json()
    invoice = data["recent_invoices"][0]

    assert "id" in invoice
    assert "invoice_number" in invoice
    assert "client_id" in invoice
    assert "amount" in invoice
    assert "status" in invoice
    assert "due_date" in invoice


# ─── Isolation ────────────────────────────────────────────────────────────────

def test_dashboard_isolation(client, auth_headers):
    """User B's dashboard is not affected by User A's data."""
    # User A creates data
    client_id = create_client(client, auth_headers)
    project_id = create_project(client, auth_headers, client_id)
    create_invoice(client, auth_headers, client_id, amount=5000.0,
                   status="paid", invoice_number="INV-001")
    create_time_entry(client, auth_headers, project_id, hours=20.0)

    # User B logs in and checks their dashboard
    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get("/analytics/dashboard", headers=user_b_headers)
    assert response.status_code == 200
    kpis = response.json()["kpis"]

    # User B sees none of User A's data
    assert kpis["total_revenue"] == 0.0
    assert kpis["total_clients"] == 0
    assert kpis["active_projects"] == 0
    assert kpis["total_hours"] == 0.0