"""Authentication routes for login/logout."""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database.db import get_db
from app.utils.auth_utils import authenticate_user, create_session_token, get_current_user, verify_password, get_password_hash
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Display login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process login form."""
    user = authenticate_user(db, username, password)

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error_message": "Ungültiger Benutzername oder Passwort"
            }
        )

    # Create session token
    token = create_session_token(user.id)

    # Create response with redirect
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="session_token",
        value=token,
        max_age=86400,  # 24 hours
        httponly=True,
        secure=True,  # Always use HTTPS for security
        samesite='strict'  # CSRF protection
    )
    return response


@router.get("/logout")
def logout(request: Request):
    """Logout user and clear session."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    return response


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request):
    """Initial setup page to create first user."""
    return templates.TemplateResponse("setup.html", {"request": request})


@router.post("/setup")
def setup_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create the first user account."""
    from app.utils.auth_utils import create_user
    from app.models.user import User

    # Check if user already exists
    existing_user = db.query(User).first()
    if existing_user:
        return templates.TemplateResponse(
            "setup.html",
            {
                "request": request,
                "error_message": "Benutzer bereits vorhanden. Bitte melden Sie sich an."
            }
        )

    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse(
            "setup.html",
            {
                "request": request,
                "error_message": "Passwörter stimmen nicht überein"
            }
        )

    # Validate password length
    if len(password) < 6:
        return templates.TemplateResponse(
            "setup.html",
            {
                "request": request,
                "error_message": "Passwort muss mindestens 6 Zeichen lang sein"
            }
        )

    try:
        # Create user
        user = create_user(db, username, email, password)

        # Auto-login after setup
        token = create_session_token(user.id)
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_token",
            value=token,
            max_age=86400,
            httponly=True,
            secure=False
        )
        return response

    except Exception as e:
        return templates.TemplateResponse(
            "setup.html",
            {
                "request": request,
                "error_message": f"Fehler beim Erstellen des Benutzers: {str(e)}"
            }
        )


@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request, db: Session = Depends(get_db)):
    """Display account settings page."""
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)

    user = get_current_user(db, token)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse("account.html", {
        "request": request,
        "user": user
    })


@router.post("/account/profile")
def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)

    user = get_current_user(db, token)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    try:
        # Update user data
        user.username = username
        user.email = email
        db.commit()

        return templates.TemplateResponse("account.html", {
            "request": request,
            "user": user,
            "success_message": "Profil erfolgreich aktualisiert"
        })
    except Exception as e:
        return templates.TemplateResponse("account.html", {
            "request": request,
            "user": user,
            "error_message": f"Fehler beim Speichern: {str(e)}"
        })


@router.post("/account/password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Change user password."""
    token = request.cookies.get("session_token")
    if not token:
        return RedirectResponse(url="/login", status_code=302)

    user = get_current_user(db, token)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Validate current password
    if not verify_password(current_password, user.hashed_password):
        return templates.TemplateResponse("account.html", {
            "request": request,
            "user": user,
            "error_message": "Aktuelles Passwort ist falsch"
        })

    # Validate new password
    if len(new_password) < 6:
        return templates.TemplateResponse("account.html", {
            "request": request,
            "user": user,
            "error_message": "Neues Passwort muss mindestens 6 Zeichen lang sein"
        })

    # Validate password confirmation
    if new_password != confirm_password:
        return templates.TemplateResponse("account.html", {
            "request": request,
            "user": user,
            "error_message": "Passwörter stimmen nicht überein"
        })

    try:
        # Update password
        user.hashed_password = get_password_hash(new_password)
        db.commit()

        return templates.TemplateResponse("account.html", {
            "request": request,
            "user": user,
            "success_message": "Passwort erfolgreich geändert"
        })
    except Exception as e:
        return templates.TemplateResponse("account.html", {
            "request": request,
            "user": user,
            "error_message": f"Fehler beim Ändern des Passworts: {str(e)}"
        })