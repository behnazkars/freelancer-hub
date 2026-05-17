# app/models/__init__.py
# Import all models here so SQLAlchemy knows about them
# when we call Base.metadata.create_all()
from app.models.user import User