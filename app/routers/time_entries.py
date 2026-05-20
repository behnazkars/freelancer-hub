# app/routers/time_entries.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.auth import get_current_user
from app.models.user import User
from app.schemas.time_entry import TimeEntryCreate, TimeEntryUpdate, TimeEntryResponse
from app.services.time_entry_service import (
    get_all_time_entries,
    get_time_entries_by_project,
    get_time_entry_by_id,
    create_time_entry,
    update_time_entry,
    delete_time_entry
)

router = APIRouter(prefix="/time-entries", tags=["Time Entries"])


@router.get("/", response_model=list[TimeEntryResponse])
def list_time_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all time entries for the logged-in user."""
    return get_all_time_entries(db, current_user.id)


@router.get("/project/{project_id}", response_model=list[TimeEntryResponse])
def list_entries_by_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all time entries for a specific project."""
    return get_time_entries_by_project(db, project_id, current_user.id)


@router.get("/{entry_id}", response_model=TimeEntryResponse)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single time entry by ID."""
    return get_time_entry_by_id(db, entry_id, current_user.id)


@router.post("/", response_model=TimeEntryResponse, status_code=201)
def log_time(
    entry_data: TimeEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log a new time entry against a project."""
    return create_time_entry(db, entry_data, current_user.id)


@router.patch("/{entry_id}", response_model=TimeEntryResponse)
def update_entry(
    entry_id: int,
    entry_data: TimeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a time entry."""
    return update_time_entry(db, entry_id, entry_data, current_user.id)


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a time entry."""
    return delete_time_entry(db, entry_id, current_user.id)