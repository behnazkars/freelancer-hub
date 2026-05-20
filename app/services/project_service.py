# app/services/project_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project import Project
from app.models.client import Client
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