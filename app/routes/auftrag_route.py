"""Order management routes for creating and managing construction projects."""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from database.db import get_db
from app.models.auftrag import Auftrag
from app.models.kunde import Kunde
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.material_komponente import MaterialKomponente
from app.models.eur_kategorie import EurKategorie
from app.models.einnahme_ausgabe import EinnahmeAusgabe
from app.utils.template_utils import create_templates
import datetime
from typing import List, Optional

router = APIRouter()
templates = create_templates()




def get_kategorie_id(db: Session, name: str, typ: str) -> int | None:
    kat = db.query(EurKategorie).filter_by(name=name, typ=typ).first()
    return kat.id if kat else None


def parse_german_decimal(value: str | float | int) -> float:
    """Convert German decimal format to float (e.g., '4,5' -> 4.5)"""
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        # Replace comma with dot and convert to float
        return float(value.replace(',', '.'))
    return 0.0


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
    berechnungsbasis: List[str] = Form(..., alias="berechnungsbasis[]"),
    anzahl_stunden: Optional[List[str]] = Form(None, alias="anzahl_stunden[]"),
    stundenlohn: Optional[List[str]] = Form(None, alias="stundenlohn[]"),
    anzahl_quadrat: Optional[List[str]] = Form(None, alias="anzahl_quadrat[]"),
    preis_pro_quadrat: Optional[List[str]] = Form(None, alias="preis_pro_quadrat[]"),
    beschreibung_liste: List[str] = Form(..., alias="beschreibung_liste[]"),

    # Material (optional)
    material_bezeichnung: Optional[List[str]] = Form(None, alias="material_bezeichnung[]"),
    material_berechnungseinheit: Optional[List[str]] = Form(
        None, alias="material_berechnungseinheit[]"),
    material_anzahl: Optional[List[str]] = Form(None, alias="material_anzahl[]"),
    material_preis_pro_einheit: Optional[List[str]] = Form(
        None, alias="material_preis_pro_einheit[]"),

    kunde_leistungsadresse: str = Form(...),
    kunde_leistung_plz: str = Form(...),
    kunde_leistung_ort: str = Form(...),

    db: Session = Depends(get_db)
):
    # Kategorien serverseitig bestimmen
    erloese_id = get_kategorie_id(db, "Erlöse", "einnahme")
    material_erloese_id = get_kategorie_id(db, "Materialerlöse", "einnahme")
    materialkosten_id = get_kategorie_id(db, "Materialkosten", "ausgabe")

    # Find the earliest start date from all work components
    start_dates = [datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in komponente_start]
    earliest_start_date = min(start_dates) if start_dates else datetime.date.today()

    neuer_auftrag = Auftrag(
        kunde_id=kunde_id,
        beschreibung=auftragsbeschreibung,
        auftrag_start=earliest_start_date,
        kunde_leistungsadresse=kunde_leistungsadresse,
        kunde_leistung_plz=kunde_leistung_plz,
        kunde_leistung_ort=kunde_leistung_ort
    )
    db.add(neuer_auftrag)
    db.commit()
    db.refresh(neuer_auftrag)

    for i in range(len(komponente_start)):
        start = datetime.datetime.strptime(
            komponente_start[i], "%Y-%m-%d").date()
        ende = datetime.datetime.strptime(
            komponente_ende[i], "%Y-%m-%d").date()
        
        # Get the appropriate values based on calculation method
        basis = berechnungsbasis[i]
        stunden_val = None
        lohn_val = None  
        quadrat_val = None
        preis_quadrat_val = None
        
        if basis == "stunden":
            stunden_val = parse_german_decimal(anzahl_stunden[i] if anzahl_stunden and i < len(anzahl_stunden) else "0")
            lohn_val = parse_german_decimal(stundenlohn[i] if stundenlohn and i < len(stundenlohn) else "0")
        elif basis == "quadratmeter":
            quadrat_val = parse_german_decimal(anzahl_quadrat[i] if anzahl_quadrat and i < len(anzahl_quadrat) else "0")
            preis_quadrat_val = parse_german_decimal(preis_pro_quadrat[i] if preis_pro_quadrat and i < len(preis_pro_quadrat) else "0")
        
        ak = ArbeitKomponente(
            auftrag_id=neuer_auftrag.id,
            komponente_start=start,
            komponente_ende=ende,
            arbeit=arbeit[i],
            berechnungsbasis=basis,
            anzahl_stunden=stunden_val,
            stundenlohn=lohn_val,
            anzahl_quadrat=quadrat_val,
            preis_pro_quadrat=preis_quadrat_val,
            beschreibung=beschreibung_liste[i],
            kategorie_id=erloese_id
        )
        db.add(ak)

    # Material-Komponenten hinzufügen (ohne automatische Kostenbuchung)
    if material_bezeichnung:
        for i in range(len(material_bezeichnung)):
            if not material_bezeichnung[i] or not material_bezeichnung[i].strip():
                continue
            
            anzahl = parse_german_decimal(
                material_anzahl[i] if material_anzahl and i < len(material_anzahl) and material_anzahl[i] else "1.0"
            )
            preis_pro_einheit = parse_german_decimal(
                material_preis_pro_einheit[i] if material_preis_pro_einheit and i < len(material_preis_pro_einheit) and material_preis_pro_einheit[i] else "0.0"
            )
            
            mk = MaterialKomponente(
                auftrag_id=neuer_auftrag.id,
                bezeichnung=material_bezeichnung[i],
                berechnungseinheit=(
                    material_berechnungseinheit[i]
                    if material_berechnungseinheit and i < len(material_berechnungseinheit) else None
                ),
                anzahl=anzahl,
                preis_pro_einheit=preis_pro_einheit,
                kategorie_id=material_erloese_id)
            db.add(mk)

    db.commit()
    return RedirectResponse("/auftrag", status_code=303)
