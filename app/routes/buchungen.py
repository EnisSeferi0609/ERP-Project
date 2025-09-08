from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from collections import defaultdict
from typing import Optional

from database.db import get_db
from app.models.einnahme_ausgabe import EinnahmeAusgabe
from app.models.eur_kategorie import EurKategorie
from app.models.rechnung import Rechnung

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")



# Formular für neue Buchung
@router.get("/buchungen/neu", response_class=HTMLResponse)
def formular_anzeigen(request: Request, db: Session = Depends(get_db)):
    kategorien = db.query(EurKategorie).order_by(
        EurKategorie.typ, EurKategorie.name).all()
    return templates.TemplateResponse("neue_buchung.html", {
        "request": request,
        "kategorien": kategorien
    })


# Neue Buchung speichern
@router.post("/buchungen")
def formular_absenden(
    datum: date = Form(...),
    betrag: float = Form(...),
    typ: str = Form(...),
    kategorie_id: int = Form(...),
    beschreibung: str = Form(""),
    db: Session = Depends(get_db)
):
    buchung = EinnahmeAusgabe(
        datum=datum,
        betrag=betrag,
        typ=typ.lower(),
        kategorie_id=kategorie_id,
        beschreibung=beschreibung
    )
    db.add(buchung)
    db.commit()
    return RedirectResponse("/euer", status_code=303)


# Rechnung als bezahlt/unbezahlt markieren & Buchung erzeugen
@router.post("/rechnung/{rechnung_id}/status")
def rechnung_status_toggle(
    rechnung_id: int, 
    payment_date: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    rechnung = db.query(Rechnung).filter(Rechnung.id == rechnung_id).first()
    if not rechnung:
        return HTMLResponse("Nicht gefunden", status_code=404)

    # Wenn von bezahlt auf unbezahlt gewechselt wird, vorherige Buchungen löschen
    if rechnung.bezahlt:  # War vorher bezahlt, wird jetzt unbezahlt
        # Alle Buchungen zu dieser Rechnung löschen
        alte_buchungen = db.query(EinnahmeAusgabe).filter_by(rechnung_id=rechnung.id).all()
        for buchung in alte_buchungen:
            db.delete(buchung)
    
    rechnung.bezahlt = not rechnung.bezahlt
    
    # Set payment date when marking as paid
    if rechnung.bezahlt and payment_date:
        try:
            rechnung.payment_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
        except ValueError:
            rechnung.payment_date = date.today()
    elif not rechnung.bezahlt:
        # Clear payment date when marking as unpaid
        rechnung.payment_date = None
    
    db.commit()

    # Falls bezahlt, automatisch EÜR-Buchungen für Material und Arbeit erzeugen
    if rechnung.bezahlt:
        # Parse payment date or use today as fallback
        booking_date = date.today()
        if payment_date:
            try:
                booking_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
            except ValueError:
                # If date parsing fails, use today
                booking_date = date.today()
        # Kategorie für Arbeitserlöse
        erloese_kategorie = db.query(EurKategorie).filter_by(
            name="Erlöse", typ="einnahme").first()
        # Kategorie für Materialerlöse  
        material_erloese_kategorie = db.query(EurKategorie).filter_by(
            name="Materialerlöse", typ="einnahme").first()
            
        if rechnung.auftrag:
            # Separate Buchung für Materialerlöse
            material_summe = sum(
                mk.anzahl * mk.preis_pro_einheit 
                for mk in rechnung.auftrag.materialien
            )
            if material_summe > 0 and material_erloese_kategorie:
                material_buchung = EinnahmeAusgabe(
                    datum=booking_date,
                    betrag=material_summe,
                    typ="einnahme",
                    kategorie_id=material_erloese_kategorie.id,
                    beschreibung=f"Materialerlöse Rechnung {rechnung.id}",
                    rechnung_id=rechnung.id
                )
                db.add(material_buchung)
            
            # Separate Buchung für Arbeitserlöse
            arbeits_summe = sum(
                ak.anzahl_stunden * ak.stundenlohn 
                for ak in rechnung.auftrag.arbeit_komponenten
            )
            if arbeits_summe > 0 and erloese_kategorie:
                arbeits_buchung = EinnahmeAusgabe(
                    datum=booking_date,
                    betrag=arbeits_summe,
                    typ="einnahme",
                    kategorie_id=erloese_kategorie.id,
                    beschreibung=f"Arbeitserlöse Rechnung {rechnung.id}",
                    rechnung_id=rechnung.id
                )
                db.add(arbeits_buchung)
        
        db.commit()

    return RedirectResponse("/rechnungsliste", status_code=303)


@router.get("/euer", response_class=HTMLResponse)
def euer_uebersicht(request: Request, view: str = "list", year: int = None, db: Session = Depends(get_db)):
    # Get all available years from the database
    all_entries = db.query(EinnahmeAusgabe).all()
    available_years = sorted(set(entry.datum.year for entry in all_entries), reverse=True)
    
    # If no year specified, use the most recent year with data
    if year is None and available_years:
        year = available_years[0]
    elif year is None:
        year = date.today().year
    
    # Filter entries by year
    eintraege = db.query(EinnahmeAusgabe).filter(
        func.strftime('%Y', EinnahmeAusgabe.datum) == str(year)
    ).order_by(EinnahmeAusgabe.datum.desc()).all()

    # Group entries by invoice
    grouped_entries = {}
    manual_entries = []
    
    for entry in eintraege:
        if entry.rechnung_id:
            if entry.rechnung_id not in grouped_entries:
                grouped_entries[entry.rechnung_id] = {
                    'rechnung': entry.rechnung,
                    'entries': []
                }
            grouped_entries[entry.rechnung_id]['entries'].append(entry)
        else:
            manual_entries.append(entry)

    einnahmen_summe = sum(
        e.betrag for e in eintraege if e.typ.lower() == "einnahme")
    ausgaben_summe = sum(
        e.betrag for e in eintraege if e.typ.lower() == "ausgabe")
    saldo = einnahmen_summe - ausgaben_summe

    from collections import defaultdict
    monate = defaultdict(lambda: {"einnahme": 0, "ausgabe": 0})
    for e in eintraege:
        key = e.datum.strftime('%Y-%m')
        if e.typ.lower() == "einnahme":
            monate[key]["einnahme"] += e.betrag
        elif e.typ.lower() == "ausgabe":
            monate[key]["ausgabe"] += e.betrag

    labels = sorted(monate.keys())
    daten_einnahmen = [monate[m]["einnahme"] for m in labels]
    daten_ausgaben = [monate[m]["ausgabe"] for m in labels]

    return templates.TemplateResponse("euer_uebersicht.html", {
        "request": request,
        "view": view,
        "year": year,
        "available_years": available_years,
        "eintraege": eintraege,
        "grouped_entries": grouped_entries,
        "manual_entries": manual_entries,
        "einnahmen_summe": einnahmen_summe,
        "ausgaben_summe": ausgaben_summe,
        "saldo": saldo,
        "labels": labels,
        "daten_einnahmen": daten_einnahmen,
        "daten_ausgaben": daten_ausgaben
    })
