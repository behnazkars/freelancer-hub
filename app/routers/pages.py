# app/routers/pages.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR  = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(tags=["Pages"])


@router.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse(url="/dashboard")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={"active_page": "dashboard"}
    )


@router.get("/clients", response_class=HTMLResponse)
def clients_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="clients/index.html",
        context={"active_page": "clients"}
    )


@router.get("/projects", response_class=HTMLResponse)
def projects_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="projects/index.html",
        context={"active_page": "projects"}
    )


@router.get("/time-entries", response_class=HTMLResponse)
def time_entries_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="time_entries/index.html",
        context={"active_page": "time"}
    )


@router.get("/invoices", response_class=HTMLResponse)
def invoices_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="invoices/index.html",
        context={"active_page": "invoices"}
    )


@router.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    return HTMLResponse("""
        <script>
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        </script>
    """)