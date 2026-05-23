# app/services/time_entry_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.time_entry import TimeEntry
from app.models.project import Project
from app.schemas.time_entry import TimeEntryCreate, TimeEntryUpdate


def get_all_time_entries(db: Session, user_id: int) -> list[TimeEntry]:
    """Get all time entries for the logged-in user."""
    return db.query(TimeEntry).filter(TimeEntry.user_id == user_id).all()


def get_time_entries_by_project(
    db: Session,
    project_id: int,
    user_id: int
) -> list[TimeEntry]:
    """
    Get all time entries for a specific project.
    Useful for showing a project's full time log.
    """
    return db.query(TimeEntry).filter(
        TimeEntry.project_id == project_id,
        TimeEntry.user_id == user_id
    ).all()


def get_time_entry_by_id(
    db: Session,
    entry_id: int,
    user_id: int
) -> TimeEntry:
    """Get a single time entry — always filter by user_id for security."""
    entry = db.query(TimeEntry).filter(
        TimeEntry.id == entry_id,
        TimeEntry.user_id == user_id
    ).first()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time entry not found"
        )
    return entry


def create_time_entry(
    db: Session,
    entry_data: TimeEntryCreate,
    user_id: int
) -> TimeEntry:
    """
    Log a new time entry.
    Verifies the project exists and belongs to this user
    before creating the entry.
    """
    # Security check — project must belong to this user
    project = db.query(Project).filter(
        Project.id == entry_data.project_id,
        Project.user_id == user_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or does not belong to you"
        )

    new_entry = TimeEntry(
        **entry_data.model_dump(),
        user_id=user_id
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def update_time_entry(
    db: Session, entry_id: int, entry_data: TimeEntryUpdate, user_id: int
) -> TimeEntry:
    """Update a time entry."""
    entry = get_time_entry_by_id(db, entry_id, user_id)

    update_data = entry_data.model_dump(exclude_unset=True)

    # Convert date string to Python date object if present
    # We accept date as string in the schema to avoid Pydantic v2
    # Optional[date] coercion bug, so we convert manually here
    if "date" in update_data and isinstance(update_data["date"], str):
        from datetime import date as date_type
        update_data["date"] = date_type.fromisoformat(update_data["date"])

    for field, value in update_data.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return entry


def delete_time_entry(db: Session, entry_id: int, user_id: int) -> dict:
    """Delete a time entry."""
    entry = get_time_entry_by_id(db, entry_id, user_id)
    db.delete(entry)
    db.commit()
    return {"message": "Time entry deleted successfully"}