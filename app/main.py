# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import engine, Base
from app.routers import auth,  clients, projects, time_entries, invoices, analytics, pages



# Import models so Base knows about them before create_all
import app.models  # noqa: F401

# Create the FastAPI application instance
# This is the core object — everything plugs into it
app = FastAPI(
    title=settings.app_name,
    description="A business management hub for freelancers.",
    version="0.1.0",
    debug=settings.debug,
)

# Create all database tables on startup
# If the table already exists, it does nothing (safe to run repeatedly)
Base.metadata.create_all(bind=engine)

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