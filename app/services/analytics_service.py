# app/services/analytics_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.client import Client
from app.models.project import Project, ProjectStatus
from app.models.time_entry import TimeEntry
from app.models.invoice import Invoice, InvoiceStatus


def get_dashboard_analytics(db: Session, user_id: int) -> dict:
    """
    Gather all KPI data for the dashboard in one function.
    We make several targeted queries rather than loading
    all records into Python — this is much faster at scale.
    """

    # ── Total revenue (sum of all paid invoices) ──────────────────
    total_revenue = db.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.user_id == user_id,
        Invoice.status == InvoiceStatus.paid
    ).scalar() or 0.0

    # ── Unpaid amount (sent + overdue invoices) ───────────────────
    unpaid_amount = db.query(
        func.sum(Invoice.total_amount)
    ).filter(
        Invoice.user_id == user_id,
        Invoice.status.in_([InvoiceStatus.sent, InvoiceStatus.overdue])
    ).scalar() or 0.0

    # ── Active project count ──────────────────────────────────────
    active_projects = db.query(func.count(Project.id)).filter(
        Project.user_id == user_id,
        Project.status == ProjectStatus.active
    ).scalar() or 0

    # ── Total clients ─────────────────────────────────────────────
    total_clients = db.query(func.count(Client.id)).filter(
        Client.user_id == user_id
    ).scalar() or 0

    # ── Total hours logged ────────────────────────────────────────
    total_hours = db.query(
        func.sum(TimeEntry.hours)
    ).filter(
        TimeEntry.user_id == user_id
    ).scalar() or 0.0

    # ── Overdue invoice count ─────────────────────────────────────
    overdue_count = db.query(func.count(Invoice.id)).filter(
        Invoice.user_id == user_id,
        Invoice.status == InvoiceStatus.overdue
    ).scalar() or 0

    # ── Revenue by client (top 5) ─────────────────────────────────
    revenue_by_client = db.query(
        Client.name,
        func.sum(Invoice.total_amount).label("total")
    ).join(
        Invoice, Invoice.client_id == Client.id
    ).filter(
        Invoice.user_id == user_id,
        Invoice.status == InvoiceStatus.paid
    ).group_by(
        Client.name
    ).order_by(
        func.sum(Invoice.total_amount).desc()
    ).limit(5).all()

    # ── Hours by project (top 5) ──────────────────────────────────
    hours_by_project = db.query(
        Project.name,
        func.sum(TimeEntry.hours).label("total")
    ).join(
        TimeEntry, TimeEntry.project_id == Project.id
    ).filter(
        TimeEntry.user_id == user_id
    ).group_by(
        Project.name
    ).order_by(
        func.sum(TimeEntry.hours).desc()
    ).limit(5).all()

    # ── Recent invoices (last 5) ──────────────────────────────────
    recent_invoices = db.query(Invoice).filter(
        Invoice.user_id == user_id
    ).order_by(
        Invoice.created_at.desc()
    ).limit(5).all()

    return {
        "kpis": {
            "total_revenue": round(total_revenue, 2),
            "unpaid_amount": round(unpaid_amount, 2),
            "active_projects": active_projects,
            "total_clients": total_clients,
            "total_hours": round(total_hours, 2),
            "overdue_invoices": overdue_count,
        },
        "revenue_by_client": [
            {"name": row.name, "total": round(row.total, 2)}
            for row in revenue_by_client
        ],
        "hours_by_project": [
            {"name": row.name, "total": round(row.total, 2)}
            for row in hours_by_project
        ],
        "recent_invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "client_id": inv.client_id,
                "amount": inv.total_amount,
                "status": inv.status,
                "due_date": str(inv.due_date),
            }
            for inv in recent_invoices
        ],
    }