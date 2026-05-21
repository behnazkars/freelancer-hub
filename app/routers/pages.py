# app/routers/pages.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=RedirectResponse)
def root():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/dashboard")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={"active_page": "dashboard"}
    )


@router.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    return HTMLResponse("""
        <script>
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        </script>
    """)