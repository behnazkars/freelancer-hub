# app/routers/clients.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.auth import get_current_user
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.services.client_service import (
    get_all_clients,
    get_client_by_id,
    create_client,
    update_client,
    delete_client
)

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=list[ClientResponse])
def list_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all clients for the logged-in user."""
    return get_all_clients(db, current_user.id)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single client by ID."""
    return get_client_by_id(db, client_id, current_user.id)


@router.post("/", response_model=ClientResponse, status_code=201)
def create_new_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new client."""
    return create_client(db, client_data, current_user.id)


@router.patch("/{client_id}", response_model=ClientResponse)
def update_existing_client(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a client. Only send the fields you want to change."""
    return update_client(db, client_id, client_data, current_user.id)


@router.delete("/{client_id}")
def delete_existing_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a client and all associated data."""
    return delete_client(db, client_id, current_user.id)