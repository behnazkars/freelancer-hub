# app/routers/frontend_dashboard.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.client import Client
from app.models.project import Project, ProjectStatus
from app.models.time_entry import TimeEntry
from app.models.invoice import Invoice, InvoiceStatus
from app.auth.auth import decode_access_token

router = APIRouter(tags=["Frontend Dashboard"])
templates = Jinja2Templates(directory="templates")


def get_current_user_from_cookie(request: Request, db: Session):
    """
    Get the current user from the cookie instead of
    the Authorization header. This is how browser-based
    auth works — the cookie is sent automatically with
    every request.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    email = decode_access_token(token)
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()


@router.get("/", response_class=HTMLResponse)
def root(request: Request, db: Session = Depends(get_db)):
    """Redirect root to dashboard or login."""
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/auth/login", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Render the main dashboard with analytics."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)

    # ─── KPI Stats ───────────────────────────────────────────────
    total_clients = db.query(Client).filter(
        Client.user_id == user.id
    ).count()

    active_projects = db.query(Project).filter(
        Project.user_id == user.id,
        Project.status == ProjectStatus.active
    ).count()

    total_hours = db.query(TimeEntry).filter(
        TimeEntry.user_id == user.id
    ).all()
    hours_sum = sum(t.hours for t in total_hours)

    paid_invoices = db.query(Invoice).filter(
        Invoice.user_id == user.id,
        Invoice.status == InvoiceStatus.paid
    ).all()
    total_revenue = sum(i.total_amount for i in paid_invoices)

    # ─── Revenue chart — last 6 months ───────────────────────────
    labels = []
    values = []
    for i in range(5, -1, -1):
        # Calculate first and last day of each month
        today = date.today()
        first_day = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        if first_day.month == 12:
            last_day = first_day.replace(day=31)
        else:
            last_day = first_day.replace(
                month=first_day.month + 1, day=1
            ) - timedelta(days=1)

        month_revenue = sum(
            inv.total_amount for inv in db.query(Invoice).filter(
                Invoice.user_id == user.id,
                Invoice.status == InvoiceStatus.paid,
                Invoice.paid_date >= first_day,
                Invoice.paid_date <= last_day
            ).all()
        )
        labels.append(first_day.strftime("%b %Y"))
        values.append(month_revenue)

    # ─── Project status chart ─────────────────────────────────────
    all_projects = db.query(Project).filter(
        Project.user_id == user.id
    ).all()

    status_counts = {
        "Active": 0, "Completed": 0, "On Hold": 0, "Cancelled": 0
    }
    for p in all_projects:
        if p.status == ProjectStatus.active:
            status_counts["Active"] += 1
        elif p.status == ProjectStatus.completed:
            status_counts["Completed"] += 1
        elif p.status == ProjectStatus.on_hold:
            status_counts["On Hold"] += 1
        elif p.status == ProjectStatus.cancelled:
            status_counts["Cancelled"] += 1

    # ─── Recent invoices ──────────────────────────────────────────
    recent_invoices = db.query(Invoice).filter(
        Invoice.user_id == user.id
    ).order_by(Invoice.created_at.desc()).limit(5).all()

    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "user": user,
        "active_page": "dashboard",
        "today": date.today().strftime("%B %d, %Y"),
        "stats": {
            "total_clients": total_clients,
            "active_projects": active_projects,
            "total_hours": hours_sum,
            "total_revenue": total_revenue,
        },
        "revenue_chart_data": {"labels": labels, "values": values},
        "status_chart_data": {
            "labels": list(status_counts.keys()),
            "values": list(status_counts.values())
        },
        "recent_invoices": recent_invoices,
    })