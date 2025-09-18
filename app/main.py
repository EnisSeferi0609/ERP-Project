"""FastAPI application for BuildFlow ERP construction management system."""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json
import logging

from sqlalchemy.orm import Session
from database.db import get_db
from app.utils.logging_config import setup_logging
from app.routes import (
    kunde_route, auftrag_route, rechnung_route,
    unternehmensdaten_route, startseite_route,
    auftrag_loeschen, buchungen, dashboard_route, health, auth_route
)
from config import config

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

logger = setup_logging()

app = FastAPI()
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)} - {request.url}", exc_info=True)
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 500, "detail": "Ein interner Fehler ist aufgetreten"},
        status_code=500
    )
app.mount(
    "/static",
    StaticFiles(
        directory=str(
            PROJECT_ROOT /
            "static")),
    name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def from_json(value):
    if value:
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return []
    return []

templates.env.filters['from_json'] = from_json


@app.get("/", response_class=HTMLResponse)
def startseite(request: Request, db: Session = Depends(get_db)):
    from app.utils.auth_middleware import check_setup_required
    from fastapi.responses import RedirectResponse

    # Check if setup is required
    if check_setup_required(db):
        return RedirectResponse(url="/setup", status_code=302)

    # Check if user is logged in
    from app.utils.auth_middleware import optional_auth
    user = optional_auth(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "startseite.html", {
            "request": request})


@app.get("/receipts/{filename}")
def serve_receipt_file(filename: str):
    """Serve receipt files from the receipts directory."""
    file_path = config.RECEIPTS_DIR / filename
    if not file_path.exists():
        return HTMLResponse("Datei nicht gefunden", status_code=404)
    
    # Security check: ensure file is within receipts directory
    try:
        file_path.resolve().relative_to(config.RECEIPTS_DIR.resolve())
    except ValueError:
        return HTMLResponse("Zugriff verweigert", status_code=403)
    
    return FileResponse(file_path)


# Include authentication routes first (no auth required)
app.include_router(auth_route.router)
app.include_router(health.router)

# Include protected routes
app.include_router(dashboard_route.router)
app.include_router(kunde_route.router)
app.include_router(auftrag_route.router)
app.include_router(rechnung_route.router)
app.include_router(unternehmensdaten_route.router)
app.include_router(startseite_route.router)
app.include_router(auftrag_loeschen.router)
app.include_router(buchungen.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
