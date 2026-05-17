# app/models/__init__.py
# All models must be imported here so SQLAlchemy's Base
# knows about every table before create_all() is called.
# Order matters — import parent tables before child tables.
from app.models.user import User
from app.models.client import Client
from app.models.project import Project, ProjectStatus
from app.models.time_entry import TimeEntry
from app.models.invoice import Invoice, InvoiceStatus