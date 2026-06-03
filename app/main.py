# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.config import settings
from app.database import engine, Base
from app.routers import auth,  clients, projects, time_entries, invoices, analytics, pages

from alembic.config import Config
from alembic import command


# Import models so Base knows about them before create_all
import app.models  # noqa: F401

BASE_DIR      = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR    = BASE_DIR / "static"

# Create the FastAPI application instance
# This is the core object — everything plugs into it
app = FastAPI(
    title=settings.app_name,
    description="A business management hub for freelancers.",
    version="0.1.0",
    debug=settings.debug,
)

# CORS — controls which domains can talk to your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run database migrations on startup
# This replaces Base.metadata.create_all() — Alembic handles everything now
# alembic upgrade head is idempotent — safe to run on every startup
def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

run_migrations()

# Mount the static files directory
# Any file in /static/ is now served at /static/filename
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Register routers — each router handles a group of related endpoints
# API routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(time_entries.router)
app.include_router(invoices.router)
app.include_router(analytics.router)

# Page router last — catches all remaining routes
app.include_router(pages.router)

# A simple health-check endpoint
# This is industry standard — every production API has one
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}


# Root endpoint — temporary, we'll replace this with a real dashboard
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}"}