# app/services/time_entry_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.time_entry import TimeEntry
from app.models.project import Project
from app.schemas.time_entry import TimeEntryCreate, TimeEntryUpdate


def _calculate_duration(start_time, end_time) -> float:
    """Calculate duration in hours, rounded to 2 decimal places."""
    delta = end_time - start_time
    return round(delta.total_seconds() / 3600, 2)


def get_all_time_entries(db: Session, user_id: int) -> list[TimeEntry]:
    """Get all time entries for the logged-in user."""
    return db.query(TimeEntry).filter(TimeEntry.user_id == user_id).all()


def get_time_entries_by_project(
    db: Session,
    project_id: int,
    user_id: int
) -> list[TimeEntry]:
    """Get all time entries for a specific project."""
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
    Create a new time entry.
    Duration is calculated automatically from start_time and end_time.
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

    duration = _calculate_duration(entry_data.start_time, entry_data.end_time)

    new_entry = TimeEntry(
        **entry_data.model_dump(),
        user_id=user_id,
        duration=duration        # injected — not from user input
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def update_time_entry(
    db: Session,
    entry_id: int,
    entry_data: TimeEntryUpdate,
    user_id: int
) -> TimeEntry:
    """
    Update a time entry.
    If start_time or end_time changes, duration is recalculated automatically.
    """
    entry = get_time_entry_by_id(db, entry_id, user_id)

    update_data = entry_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(entry, field, value)

    # Recalculate duration if either time changed
    if "start_time" in update_data or "end_time" in update_data:
        entry.duration = _calculate_duration(entry.start_time, entry.end_time)

    db.commit()
    db.refresh(entry)
    return entry


def delete_time_entry(db: Session, entry_id: int, user_id: int) -> dict:
    """Delete a time entry."""
    entry = get_time_entry_by_id(db, entry_id, user_id)
    db.delete(entry)
    db.commit()
    return {"message": "Time entry deleted successfully"}