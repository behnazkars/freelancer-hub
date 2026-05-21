# app/routers/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.auth import get_current_user
from app.models.user import User
from app.services.analytics_service import get_dashboard_analytics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns all KPI data for the dashboard in one request.
    Keeping it as one endpoint means one network call
    from the frontend — faster and simpler than 4 separate calls.
    """
    return get_dashboard_analytics(db, current_user.id)