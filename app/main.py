# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings

# Create the FastAPI application instance
# This is the core object — everything plugs into it
app = FastAPI(
    title=settings.app_name,
    description="A business management hub for freelancers.",
    version="0.1.0",
    debug=settings.debug,
)

# Mount the static files directory
# Any file in /static/ is now served at /static/filename
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


# A simple health-check endpoint
# This is industry standard — every production API has one
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}


# Root endpoint — temporary, we'll replace this with a real dashboard
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name}"}