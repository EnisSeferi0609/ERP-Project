from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

from sqlalchemy.orm import Session
from database.db import get_db
from app.models import Unternehmensstatistik

from app.routes import kunde_route, auftrag_route, rechnung_route, unternehmensdaten_route, startseite_route, auftrag_loeschen

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
def startseite(request: Request, db: Session = Depends(get_db)):
    daten_roh = db.query(Unternehmensstatistik).order_by(Unternehmensstatistik.datum.desc()).all()
    daten = [
        {
            "datum": eintrag.datum.strftime("%Y-%m-%d"),
            "kategorie": eintrag.kategorie.value,
            "wert": eintrag.wert,
            "einheit": eintrag.einheit
        }
        for eintrag in daten_roh
    ]
    return templates.TemplateResponse("startseite.html", {"request": request, "daten": daten})

app.include_router(kunde_route.router)
app.include_router(auftrag_route.router)
app.include_router(rechnung_route.router)
app.include_router(unternehmensdaten_route.router)
app.include_router(startseite_route.router)
app.include_router(auftrag_loeschen.router)
