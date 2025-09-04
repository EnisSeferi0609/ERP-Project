from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database.db import get_db
from app.models import Unternehmensstatistik

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    daten = db.query(Unternehmensstatistik).order_by(
        Unternehmensstatistik.datum.desc()).all()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "daten": daten
    })
