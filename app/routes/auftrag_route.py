from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from database.db import SessionLocal
from app.models.auftrag import Auftrag
from app.models.kunde import Kunde
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.material_komponente import MaterialKomponente
from app.models.eur_kategorie import EurKategorie
from fastapi.templating import Jinja2Templates
from pathlib import Path
import datetime, os
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

def get_kategorie_id(db: Session, name: str, typ: str) -> int | None:
    kat = db.query(EurKategorie).filter_by(name=name, typ=typ).first()
    return kat.id if kat else None

@router.get("/auftrag", response_class=HTMLResponse)
def formular_auftrag(request: Request, db: Session = Depends(get_db)):
    kunden = db.query(Kunde).all()
    return templates.TemplateResponse(
        "formular_auftrag.html",
        {"request": request, "kunden": kunden}
    )

@router.post("/auftraege")
async def auftrag_anlegen(
    request: Request,
    kunde_id: int = Form(...),
    auftragsbeschreibung: str = Form(...),

    # Arbeit
    komponente_start: List[str] = Form(..., alias="komponente_start[]"),
    komponente_ende: List[str] = Form(..., alias="komponente_ende[]"),
    arbeit: List[str] = Form(..., alias="arbeit[]"),
    anzahl_stunden: List[int] = Form(..., alias="anzahl_stunden[]"),
    stundenlohn: List[float] = Form(..., alias="stundenlohn[]"),
    beschreibung_liste: List[str] = Form(..., alias="beschreibung_liste[]"),

    # Material (optional)
    material_bezeichnung: List[str] = Form([], alias="material_bezeichnung[]"),
    material_berechnungseinheit: List[str] = Form([], alias="material_berechnungseinheit[]"),
    material_preis_pro_einheit: List[float] = Form([], alias="material_preis_pro_einheit[]"),

    kunde_leistungsadresse: str = Form(...),
    kunde_leistung_plz: str = Form(...),
    kunde_leistung_ort: str = Form(...),

    db: Session = Depends(get_db)
):
    # Kategorien serverseitig bestimmen
    erloese_id = get_kategorie_id(db, "Erlöse", "einnahme")
    material_erloese_id = get_kategorie_id(db, "Materialerlöse", "einnahme")

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
        start = datetime.datetime.strptime(komponente_start[i], "%Y-%m-%d").date()
        ende = datetime.datetime.strptime(komponente_ende[i], "%Y-%m-%d").date()
        ak = ArbeitKomponente(
            auftrag_id=neuer_auftrag.id,
            komponente_start=start,
            komponente_ende=ende,
            arbeit=arbeit[i],
            anzahl_stunden=anzahl_stunden[i],
            stundenlohn=stundenlohn[i],
            beschreibung=beschreibung_liste[i],
            kategorie_id=erloese_id
        )
        db.add(ak)

    for i in range(len(material_bezeichnung)):
        if not material_bezeichnung[i].strip():
            continue
        mk = MaterialKomponente(
            auftrag_id=neuer_auftrag.id,
            bezeichnung=material_bezeichnung[i],
            berechnungseinheit=material_berechnungseinheit[i] if i < len(material_berechnungseinheit) else None,
            preis_pro_einheit=material_preis_pro_einheit[i] if i < len(material_preis_pro_einheit) else None,
            kategorie_id=material_erloese_id
        )
        db.add(mk)

    db.commit()
    return RedirectResponse("/auftrag", status_code=303)
