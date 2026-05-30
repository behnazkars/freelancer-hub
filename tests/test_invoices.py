# tests/test_invoices.py
from datetime import date


# ─── Helpers ─────────────────────────────────────────────────────────────────

def create_client(client, auth_headers, name="Acme Corp"):
    response = client.post("/clients/", json={
        "name": name,
        "email": "acme@example.com"
    }, headers=auth_headers)
    return response.json()["id"]


def create_invoice(client, auth_headers, client_id, amount=1000.0,
                   tax_rate=0.0, invoice_number="INV-001"):
    response = client.post("/invoices/", json={
        "client_id": client_id,
        "invoice_number": invoice_number,
        "amount": amount,
        "tax_rate": tax_rate,
        "issue_date": str(date.today()),
        "due_date": str(date.today()),
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

def test_create_invoice_success(client, auth_headers):
    """An authenticated user can create an invoice for their own client."""
    client_id = create_client(client, auth_headers)
    response = client.post("/invoices/", json={
        "client_id": client_id,
        "invoice_number": "INV-001",
        "amount": 1000.0,
        "tax_rate": 0.0,
        "issue_date": str(date.today()),
        "due_date": str(date.today()),
    }, headers=auth_headers)
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["invoice_number"] == "INV-001"
    assert data["amount"] == 1000.0
    assert data["status"] == "draft"   # always starts as draft
    assert "id" in data


def test_create_invoice_requires_auth(client, auth_headers):
    """Creating an invoice without a token is rejected."""
    client_id = create_client(client, auth_headers)
    response = client.post("/invoices/", json={
        "client_id": client_id,
        "invoice_number": "INV-001",
        "amount": 1000.0,
        "issue_date": str(date.today()),
        "due_date": str(date.today()),
    })
    assert response.status_code == 401


def test_create_invoice_for_other_users_client(client, auth_headers):
    """Creating an invoice for another user's client is rejected with 404."""
    # User A creates a client
    client_id = create_client(client, auth_headers)

    # User B tries to invoice User A's client
    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.post("/invoices/", json={
        "client_id": client_id,   # belongs to User A
        "invoice_number": "INV-001",
        "amount": 500.0,
        "issue_date": str(date.today()),
        "due_date": str(date.today()),
    }, headers=user_b_headers)
    assert response.status_code == 404


# ─── Tax calculation ──────────────────────────────────────────────────────────

def test_invoice_total_amount_no_tax(client, auth_headers):
    """With tax_rate=0, total_amount equals amount."""
    client_id = create_client(client, auth_headers)
    data = create_invoice(client, auth_headers, client_id,
                          amount=1000.0, tax_rate=0.0)
    assert data["total_amount"] == 1000.0


def test_invoice_total_amount_with_tax(client, auth_headers):
    """total_amount = amount + (amount * tax_rate / 100)."""
    client_id = create_client(client, auth_headers)
    # 1000 + (1000 * 18 / 100) = 1000 + 180 = 1180
    data = create_invoice(client, auth_headers, client_id,
                          amount=1000.0, tax_rate=18.0)
    assert data["total_amount"] == 1180.0


def test_invoice_total_recalculated_on_update(client, auth_headers):
    """Updating amount or tax_rate recalculates total_amount correctly."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id,
                             amount=1000.0, tax_rate=0.0)
    invoice_id = invoice["id"]

    # Update amount to 2000 with 10% tax → total should be 2200
    response = client.patch(f"/invoices/{invoice_id}", json={
        "amount": 2000.0,
        "tax_rate": 10.0
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total_amount"] == 2200.0


# ─── Status transitions ───────────────────────────────────────────────────────

def test_invoice_starts_as_draft(client, auth_headers):
    """A newly created invoice always has draft status."""
    client_id = create_client(client, auth_headers)
    data = create_invoice(client, auth_headers, client_id)
    assert data["status"] == "draft"


def test_invoice_status_can_be_updated_to_sent(client, auth_headers):
    """An invoice status can be changed from draft to sent."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id)

    response = client.patch(f"/invoices/{invoice['id']}", json={
        "status": "sent"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "sent"


def test_invoice_status_can_be_updated_to_paid(client, auth_headers):
    """An invoice status can be changed to paid."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id)

    response = client.patch(f"/invoices/{invoice['id']}", json={
        "status": "paid"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "paid"


def test_invoice_status_can_be_updated_to_overdue(client, auth_headers):
    """An invoice status can be changed to overdue."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id)

    response = client.patch(f"/invoices/{invoice['id']}", json={
        "status": "overdue"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "overdue"


# ─── Read ─────────────────────────────────────────────────────────────────────

def test_list_invoices_empty(client, auth_headers):
    """A new user starts with no invoices."""
    response = client.get("/invoices/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_invoices_returns_own_invoices(client, auth_headers):
    """Listed invoices belong to the requesting user."""
    client_id = create_client(client, auth_headers)
    create_invoice(client, auth_headers, client_id,
                   amount=100.0, invoice_number="INV-001")
    create_invoice(client, auth_headers, client_id,
                   amount=200.0, invoice_number="INV-002")

    response = client.get("/invoices/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_invoice_by_id(client, auth_headers):
    """A user can fetch one of their own invoices by ID."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id)

    response = client.get(f"/invoices/{invoice['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == invoice["id"]


def test_get_nonexistent_invoice_returns_404(client, auth_headers):
    """Fetching an invoice ID that doesn't exist returns 404."""
    response = client.get("/invoices/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Update ───────────────────────────────────────────────────────────────────

def test_update_invoice_notes(client, auth_headers):
    """A user can update their invoice notes."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id)

    response = client.patch(f"/invoices/{invoice['id']}", json={
        "notes": "Please pay within 30 days"
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["notes"] == "Please pay within 30 days"


def test_update_nonexistent_invoice_returns_404(client, auth_headers):
    """Updating an invoice that doesn't exist returns 404."""
    response = client.patch("/invoices/99999", json={
        "notes": "ghost"
    }, headers=auth_headers)
    assert response.status_code == 404


# ─── Delete ───────────────────────────────────────────────────────────────────

def test_delete_invoice(client, auth_headers):
    """A user can delete their own invoice."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id)

    response = client.delete(f"/invoices/{invoice['id']}", headers=auth_headers)
    assert response.status_code in (200, 204)

    follow_up = client.get(f"/invoices/{invoice['id']}", headers=auth_headers)
    assert follow_up.status_code == 404


def test_delete_nonexistent_invoice_returns_404(client, auth_headers):
    """Deleting an invoice that doesn't exist returns 404."""
    response = client.delete("/invoices/99999", headers=auth_headers)
    assert response.status_code == 404


# ─── Ownership security ───────────────────────────────────────────────────────

def test_user_cannot_see_other_users_invoices(client, auth_headers):
    """User B cannot see User A's invoices in their list."""
    client_id = create_client(client, auth_headers)
    create_invoice(client, auth_headers, client_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get("/invoices/", headers=user_b_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_access_other_users_invoice_by_id(client, auth_headers):
    """User B cannot fetch User A's invoice directly by ID."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.get(f"/invoices/{invoice['id']}", headers=user_b_headers)
    assert response.status_code == 404


def test_user_cannot_delete_other_users_invoice(client, auth_headers):
    """User B cannot delete User A's invoice."""
    client_id = create_client(client, auth_headers)
    invoice = create_invoice(client, auth_headers, client_id)

    user_b_headers = register_and_login(
        client, "Bob", "bob@example.com", "BobPass123"
    )
    response = client.delete(f"/invoices/{invoice['id']}", headers=user_b_headers)
    assert response.status_code == 404

    # Verify it still exists for User A
    response = client.get(f"/invoices/{invoice['id']}", headers=auth_headers)
    assert response.status_code == 200