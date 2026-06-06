# app/services/project_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.project import Project
from app.models.client import Client
from app.models.time_entry import TimeEntry
from app.schemas.project import ProjectCreate, ProjectUpdate


def get_all_projects(db: Session, user_id: int) -> list[Project]:
    return db.query(Project).filter(Project.user_id == user_id).all()


def get_project_by_id(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


def create_project(db: Session, project_data: ProjectCreate, user_id: int) -> Project:
    # Verify the client exists AND belongs to this user
    # This prevents two bugs at once:
    # 1. Creating a project for a non-existent client
    # 2. Creating a project for another user's client
    client = db.query(Client).filter(
        Client.id == project_data.client_id,
        Client.user_id == user_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or does not belong to you"
        )

    new_project = Project(**project_data.model_dump(), user_id=user_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


def update_project(
    db: Session,
    project_id: int,
    project_data: ProjectUpdate,
    user_id: int
) -> Project:
    project = get_project_by_id(db, project_id, user_id)
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, user_id: int) -> dict:
    project = get_project_by_id(db, project_id, user_id)
    db.delete(project)
    db.commit()
    return {"message": f"Project '{project.name}' deleted successfully"}


def get_scope_status(db: Session, project_id: int, user_id: int) -> dict:
    """
    Calculate scope creep status for a project.

    Returns alert level based on budget_hours vs total logged hours.
    All calculations are server-side — never trusted from client.
    """
    project = get_project_by_id(db, project_id, user_id)

    # Graceful no-op: no budget set means no alert to show
    if not project.budget_hours:
        return {
            "project_id": project_id,
            "alert_level": "none",
            "message": "No budget hours set for this project.",
            "budget_hours": None,
            "logged_hours": None,
            "budget_used_percent": None,
            "projected_revenue": None,
            "actual_cost": None,
            "profit_margin": None,
        }

    # Sum all duration values for this project — server-side only
    total_logged = db.query(func.sum(TimeEntry.duration)).filter(
        TimeEntry.project_id == project_id,
        TimeEntry.user_id == user_id
    ).scalar() or 0.0

    budget_used_percent = round((total_logged / project.budget_hours) * 100, 2)

    # Profitability — server-side only, never from client input
    projected_revenue = project.budget_hours * project.hourly_rate
    actual_cost = total_logged * project.hourly_rate

    if projected_revenue > 0:
        profit_margin = round(
            ((projected_revenue - actual_cost) / projected_revenue) * 100, 2
        )
    else:
        profit_margin = None

    # Determine alert level
    if budget_used_percent >= 100:
        alert_level = "danger"
        message = f"Budget exceeded! You have used {budget_used_percent}% of your budget hours."
    elif budget_used_percent >= 80:
        alert_level = "warning"
        message = f"Warning: You have used {budget_used_percent}% of your budget hours."
    else:
        alert_level = "none"
        message = f"On track. You have used {budget_used_percent}% of your budget hours."

    return {
        "project_id": project_id,
        "alert_level": alert_level,
        "message": message,
        "budget_hours": project.budget_hours,
        "logged_hours": total_logged,
        "budget_used_percent": budget_used_percent,
        "projected_revenue": projected_revenue,
        "actual_cost": actual_cost,
        "profit_margin": profit_margin,
    }