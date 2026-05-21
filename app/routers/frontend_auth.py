# app/routers/frontend_auth.py
from fastapi import APIRouter, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.user_service import register_user, login_user
from app.schemas.user import UserRegister

router = APIRouter(tags=["Frontend Auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/auth/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request}
    )


@router.post("/auth/login-form")
def login_form(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Handle login form submission.
    On success: set JWT in a cookie and redirect to dashboard.
    On failure: re-render login page with error message.
    """
    try:
        token = login_user(db, email, password)

        # Store the token in an HTTP-only cookie
        # HTTP-only means JavaScript can't read it — more secure
        redirect = RedirectResponse(url="/dashboard", status_code=302)
        redirect.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=1800  # 30 minutes
        )
        return redirect

    except Exception:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid email or password"}
        )


@router.get("/auth/register", response_class=HTMLResponse)
def register_page(request: Request):
    """Render the register page."""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request}
    )


@router.post("/auth/register-form")
def register_form(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle registration form submission."""
    try:
        register_user(db, UserRegister(
            full_name=full_name,
            email=email,
            password=password
        ))
        # After registration, redirect to login
        return RedirectResponse(url="/auth/login", status_code=302)

    except Exception as e:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": str(e)}
        )


@router.get("/auth/logout")
def logout():
    """Clear the cookie and redirect to login."""
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response