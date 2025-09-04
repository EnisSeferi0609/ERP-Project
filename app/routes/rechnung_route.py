from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database.db import SessionLocal
from app.models.rechnung import Rechnung
from app.models.kunde import Kunde
from app.models.auftrag import Auftrag
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.unternehmensdaten import Unternehmensdaten
from app.models.material_komponente import MaterialKomponente
from sqlalchemy import false, true
from fastapi.responses import RedirectResponse
from app.models.einnahme_ausgabe import EinnahmeAusgabe
from datetime import date
from app.models.eur_kategorie import EurKategorie


import pdfkit
import datetime
import os
from pathlib import Path
import base64


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# German decimal formatting function
def format_german_decimal(value, decimals=2):
    """Format number with German decimal notation (comma instead of dot)"""
    if value is None:
        value = 0
    # Format with specified decimal places, then replace dot with comma
    formatted = f"{float(value):.{decimals}f}"
    return formatted.replace('.', ',')

# Add the filter to Jinja2 environment
templates.env.filters['german_decimal'] = format_german_decimal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/rechnung", response_class=HTMLResponse)
def formular_rechnung(request: Request, db: Session = Depends(get_db)):
    kunden = db.query(Kunde).all()
    auftraege = db.query(Auftrag).all()
    unternehmensdaten = db.query(Unternehmensdaten).first()
    return templates.TemplateResponse("formular_rechnung.html", {
        "request": request,
        "kunden": kunden,
        "auftraege": auftraege,
        "unternehmensdaten": unternehmensdaten
    })


@router.post("/rechnungen")
def rechnung_erstellen(
    request: Request,
    kunde_id: int = Form(...),
    auftrag_id: int = Form(...),
    db: Session = Depends(get_db)
):
    # Kunde & Auftrag laden
    kunde = db.query(Kunde).filter(Kunde.id == kunde_id).first()
    auftrag = db.query(Auftrag).filter(Auftrag.id == auftrag_id).first()

    komponenten = db.query(ArbeitKomponente).filter(
        ArbeitKomponente.auftrag_id == auftrag_id).all()
    materialien = db.query(MaterialKomponente).filter(
        MaterialKomponente.auftrag_id == auftrag_id).all()

    if not auftrag or not kunde or not komponenten:
        return HTMLResponse(
            content=("Auftrag oder Kunde oder Arbeitskomponenten "
                     "nicht gefunden."),
            status_code=404)
    
    # Prüfen ob bereits eine Rechnung für diesen Auftrag existiert
    existierende_rechnung = db.query(Rechnung).filter(
        Rechnung.auftrag_id == auftrag_id).first()
    
    # Summen berechnen (immer neu berechnen für aktuellste Werte)
    gesamt_arbeit = sum((k.anzahl_stunden or 0) *
                        (k.stundenlohn or 0) for k in komponenten)
    gesamt_material = sum(
        (m.preis_pro_einheit or 0) * (m.anzahl or 1)
        for m in materialien
    )

    faelligkeit = datetime.date.today() + datetime.timedelta(days=30)

    if existierende_rechnung:
        # Falls Rechnung bereits existiert, diese mit neuen Werten überschreiben
        existierende_rechnung.rechnungsdatum = datetime.date.today()
        existierende_rechnung.faelligkeit = faelligkeit
        existierende_rechnung.rechnungssumme_arbeit = gesamt_arbeit
        existierende_rechnung.rechnungssumme_material = gesamt_material
        existierende_rechnung.rechnungssumme_gesamt = gesamt_arbeit + gesamt_material
        neue_rechnung = existierende_rechnung
    else:
        # Neue Rechnung anlegen
        neue_rechnung = Rechnung(
            kunde_id=kunde.id,
            auftrag_id=auftrag.id,
            unternehmensdaten_id=1,  # Anpassen falls mehrere Unternehmen
            rechnungsdatum=datetime.date.today(),
            faelligkeit=faelligkeit,
            rechtlicher_hinweis="Zahlbar ohne Abzug innerhalb von 14 Tagen.",
            rechnungssumme_arbeit=gesamt_arbeit,
            rechnungssumme_material=gesamt_material,
            rechnungssumme_gesamt=gesamt_arbeit + gesamt_material
        )
        db.add(neue_rechnung)
    
    db.commit()
    db.refresh(neue_rechnung)

    unternehmensdaten = db.query(Unternehmensdaten).first()

    # Logo laden und Base64-kodieren
    with open("app/static/logo.png", "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    # HTML rendern
    rendered_html = templates.get_template("rechnung_template.html").render({
        "kunde": kunde,
        "auftrag": auftrag,
        "komponenten": komponenten,
        "materialien": materialien,
        "rechnung": neue_rechnung,
        "unternehmensdaten": unternehmensdaten,
        "logo_base64": logo_base64
    })

    # PDF-Ordner sicherstellen
    rechnungen_dir = os.path.join(BASE_DIR, "rechnungen")
    os.makedirs(rechnungen_dir, exist_ok=True)

    # PDF-Datei erstellen (nach Rechnungs-ID benannt)
    pdf_path = os.path.join(rechnungen_dir, f"Rechnung_{neue_rechnung.id}.pdf")
    config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")

    try:
        pdfkit.from_string(rendered_html, pdf_path, configuration=config)
    except Exception as e:
        db.rollback()
        return HTMLResponse(
            f"PDF-Generierung fehlgeschlagen: {e}",
            status_code=500)

    # PDF ausliefern
    return FileResponse(
        path=pdf_path,
        filename=f"Rechnung_{neue_rechnung.id}.pdf",
        media_type="application/pdf"
    )


@router.get("/rechnungsliste")
def rechnungsliste(
        request: Request,
        db: Session = Depends(get_db),
        status: str = None):
    query = db.query(Rechnung)
    if status == "offen":
        query = query.filter(Rechnung.bezahlt == false())
    elif status == "bezahlt":
        query = query.filter(Rechnung.bezahlt == true())

    rechnungen = query.all()

    return templates.TemplateResponse(
        "rechnung_liste.html",
        {"request": request, "rechnungen": rechnungen, "status": status}
    )


@router.post("/rechnung/{rechnung_id}/status")
def rechnung_status_toggle(rechnung_id: int, db: Session = Depends(get_db)):
    rechnung = db.query(Rechnung).filter(Rechnung.id == rechnung_id).first()
    if not rechnung:
        return HTMLResponse("Rechnung nicht gefunden", status_code=404)

    rechnung.bezahlt = not rechnung.bezahlt
    db.commit()

    if rechnung.bezahlt:
        # vorherige Einnahmen dieser Rechnung entfernen (Idempotenz)
        db.query(EinnahmeAusgabe).filter_by(
            rechnung_id=rechnung.id, typ="einnahme").delete()

        erlöse = db.query(EurKategorie).filter_by(
            name="Erlöse", typ="einnahme").first()
        mat_erlöse = db.query(EurKategorie).filter_by(
            name="Materialerlöse", typ="einnahme").first()

        eintraege = []
        if (rechnung.rechnungssumme_arbeit or 0) > 0:
            eintraege.append(EinnahmeAusgabe(
                datum=date.today(),
                typ="einnahme",
                betrag=rechnung.rechnungssumme_arbeit,
                beschreibung=f"Erlöse (Arbeit) – Rechnung #{rechnung.id}",
                zahlungsart="Bank",
                rechnung_id=rechnung.id,
                kategorie_id=erlöse.id if erlöse else None
            ))
        if (rechnung.rechnungssumme_material or 0) > 0:
            eintraege.append(EinnahmeAusgabe(
                datum=date.today(),
                typ="einnahme",
                betrag=rechnung.rechnungssumme_material,
                beschreibung=f"Materialerlöse – Rechnung #{rechnung.id}",
                zahlungsart="Bank",
                rechnung_id=rechnung.id,
                kategorie_id=mat_erlöse.id if mat_erlöse else None
            ))

        db.add_all(eintraege)
        db.commit()
    else:
        db.query(EinnahmeAusgabe).filter_by(
            rechnung_id=rechnung.id, typ="einnahme").delete()
        db.commit()

    return RedirectResponse("/rechnungsliste", status_code=303)


@router.get("/rechnung/{rechnung_id}/download")
def download_rechnung_pdf(rechnung_id: int, db: Session = Depends(get_db)):
    """Download einer spezifischen Rechnungs-PDF."""
    # Prüfe ob Rechnung existiert
    rechnung = db.query(Rechnung).filter(Rechnung.id == rechnung_id).first()
    if not rechnung:
        return HTMLResponse("Rechnung nicht gefunden", status_code=404)
    
    # Prüfe ob PDF-Datei existiert
    pdf_filename = f"Rechnung_{rechnung_id}.pdf"
    pdf_path = os.path.join(BASE_DIR, "rechnungen", pdf_filename)
    
    if not os.path.exists(pdf_path):
        return HTMLResponse("PDF-Datei nicht gefunden", status_code=404)
    
    return FileResponse(
        path=pdf_path,
        filename=pdf_filename,
        media_type='application/pdf'
    )
