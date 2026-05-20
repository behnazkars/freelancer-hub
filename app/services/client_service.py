# app/services/client_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


def get_all_clients(db: Session, user_id: int) -> list[Client]:
    """
    Get all clients belonging to a specific user.
    The user_id filter is critical — users must never
    see each other's clients.
    """
    return db.query(Client).filter(Client.user_id == user_id).all()


def get_client_by_id(db: Session, client_id: int, user_id: int) -> Client:
    """
    Get a single client by ID.
    We always filter by user_id too — this prevents a user from
    accessing another user's client just by guessing an ID.
    This is called 'Insecure Direct Object Reference' (IDOR)
    and is one of the most common security vulnerabilities.
    """
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == user_id
    ).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client


def create_client(db: Session, client_data: ClientCreate, user_id: int) -> Client:
    """Create a new client linked to the current user."""
    new_client = Client(
        **client_data.model_dump(),  # unpack all fields from the schema
        user_id=user_id
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client


def update_client(
    db: Session,
    client_id: int,
    client_data: ClientUpdate,
    user_id: int
) -> Client:
    """
    Update only the fields that were sent.
    exclude_unset=True means: only update fields the client
    actually included in the request — don't overwrite
    everything else with None.
    """
    client = get_client_by_id(db, client_id, user_id)

    update_data = client_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_id: int, user_id: int) -> dict:
    """Delete a client. Returns a confirmation message."""
    client = get_client_by_id(db, client_id, user_id)
    db.delete(client)
    db.commit()
    return {"message": f"Client '{client.name}' deleted successfully"}