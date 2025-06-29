from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.db import SessionLocal
from app.models.auftrag import Auftrag
import datetime
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
from app.models.kunde import Kunde
from app.models.arbeit_komponente import ArbeitKomponente
from typing import List


router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/auftrag", response_class=HTMLResponse)
def formular_auftrag(request: Request, db: Session = Depends(get_db)):
    kunden = db.query(Kunde).all()
    return templates.TemplateResponse("formular_auftrag.html", {"request": request, "kunden": kunden})

@router.post("/auftraege")
def auftrag_anlegen(
    request: Request,
    kunde_id: int = Form(...),
    auftragsbeschreibung: str = Form(...),
    komponente_start: List[str] = Form(...),
    komponente_ende: List[str] = Form(...),
    arbeit: List[str] = Form(...),
    anzahl_stunden: List[int] = Form(...),
    stundenlohn: List[float] = Form(...),
    beschreibung_liste: List[str] = Form(...),
    kunde_leistungsadresse: str = Form(...),
    kunde_leistung_plz: str = Form(...),
    kunde_leistung_ort: str = Form(...),
    db: Session = Depends(get_db)
):
    neuer_auftrag = Auftrag(
    kunde_id=kunde_id,
    beschreibung=auftragsbeschreibung,
    auftrag_start=datetime.date.today(),
    kunde_leistungsadresse=kunde_leistungsadresse,
    kunde_leistung_plz=kunde_leistung_plz,
    kunde_leistung_ort=kunde_leistung_ort
    )   

    db.add(neuer_auftrag)       
    db.commit()
    db.refresh(neuer_auftrag)

    for i in range(len(komponente_start)):
        komponent = ArbeitKomponente(
        auftrag_id=neuer_auftrag.id,
        komponente_start=datetime.datetime.strptime(komponente_start[i], "%Y-%m-%d").date(),
        komponente_ende=datetime.datetime.strptime(komponente_ende[i], "%Y-%m-%d").date(),
        arbeit=arbeit[i],
        anzahl_stunden=anzahl_stunden[i],
        stundenlohn=stundenlohn[i],
        beschreibung=beschreibung_liste[i]
    )
    db.add(komponent)


    db.commit()
    return RedirectResponse("/auftrag", status_code=303)
