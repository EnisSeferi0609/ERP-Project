from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from sqlalchemy.orm import Session
from database.db import get_db
from app.models import Unternehmensstatistik
from app.routes import (
    kunde_route, auftrag_route, rechnung_route,
    unternehmensdaten_route, startseite_route,
    auftrag_loeschen, buchungen
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(
        directory=str(
            PROJECT_ROOT /
            "static")),
    name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def startseite(request: Request, db: Session = Depends(get_db)):
    daten_roh = db.query(Unternehmensstatistik).order_by(
        Unternehmensstatistik.datum.desc()).all()
    daten = [
        {
            "datum": eintrag.datum.strftime("%Y-%m-%d"),
            "kategorie": eintrag.kategorie.value,
            "wert": eintrag.wert,
            "einheit": eintrag.einheit
        }
        for eintrag in daten_roh
    ]
    return templates.TemplateResponse(
        "startseite.html", {
            "request": request, "daten": daten})


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
