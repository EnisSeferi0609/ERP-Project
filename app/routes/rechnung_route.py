from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
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
import secrets
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

# Add filters to Jinja2 environment
templates.env.filters['german_decimal'] = format_german_decimal
templates.env.filters['basename'] = lambda path: os.path.basename(path) if path else ''


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

    rechnungen = query.order_by(Rechnung.id.desc()).all()

    return templates.TemplateResponse(
        "rechnung_liste.html",
        {"request": request, "rechnungen": rechnungen, "status": status}
    )



@router.get("/rechnung/{rechnung_id}/materialkosten", response_class=HTMLResponse)
def material_kosten_formular(rechnung_id: int, request: Request, db: Session = Depends(get_db)):
    """Form to enter actual material costs for a specific invoice."""
    rechnung = db.query(Rechnung).options(
        joinedload(Rechnung.kunde),
        joinedload(Rechnung.auftrag)
    ).filter(Rechnung.id == rechnung_id).first()
    if not rechnung:
        return HTMLResponse("Rechnung nicht gefunden", status_code=404)
    
    # Get all materials for this invoice's order
    materialien = db.query(MaterialKomponente).filter(
        MaterialKomponente.auftrag_id == rechnung.auftrag_id
    ).all()
    
    return templates.TemplateResponse("material_kosten_form.html", {
        "request": request,
        "rechnung": rechnung,
        "materialien": materialien
    })


@router.post("/rechnung/{rechnung_id}/materialkosten")
async def material_kosten_speichern(
    rechnung_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Save actual material costs and create expense bookings."""
    rechnung = db.query(Rechnung).filter(Rechnung.id == rechnung_id).first()
    if not rechnung:
        return HTMLResponse("Rechnung nicht gefunden", status_code=404)
    
    # Get form data
    form_data = await request.form()
    
    # Create receipts directory if it doesn't exist
    receipts_dir = os.path.join(BASE_DIR, "receipts")
    os.makedirs(receipts_dir, exist_ok=True)
    
    # Get Materialkosten category
    materialkosten_kategorie = db.query(EurKategorie).filter_by(
        name="Materialkosten", typ="ausgabe"
    ).first()
    
    # Process each material component
    materialien = db.query(MaterialKomponente).filter(
        MaterialKomponente.auftrag_id == rechnung.auftrag_id
    ).all()
    
    total_expenses = 0
    
    for material in materialien:
        # Get actual cost from form
        actual_cost_key = f"actual_cost_{material.id}"
        actual_cost = form_data.get(actual_cost_key)
        
        # Handle file upload
        receipt_key = f"receipt_{material.id}"
        receipt_file = form_data.get(receipt_key)
        
        if actual_cost and float(actual_cost) > 0:
            actual_cost_float = float(actual_cost)
            total_expenses += actual_cost_float
            
            # Update material component with actual cost
            material.actual_cost = actual_cost_float
            
            # Handle file upload if provided
            if receipt_file and hasattr(receipt_file, 'filename') and receipt_file.filename:
                # Create safe filename
                file_extension = os.path.splitext(receipt_file.filename)[1]
                safe_filename = f"receipt_{rechnung_id}_{material.id}_{secrets.token_hex(8)}{file_extension}"
                file_path = os.path.join(receipts_dir, safe_filename)
                
                # Save file
                with open(file_path, "wb") as buffer:
                    content = await receipt_file.read()
                    buffer.write(content)
                
                # Update material component with receipt path
                material.receipt_path = safe_filename
            
            # Create expense booking
            expense_booking = EinnahmeAusgabe(
                datum=date.today(),
                betrag=actual_cost_float,
                typ="ausgabe",
                kategorie_id=materialkosten_kategorie.id if materialkosten_kategorie else None,
                beschreibung=f"Materialkosten {material.bezeichnung} - Rechnung #{rechnung_id}",
                rechnung_id=rechnung_id
            )
            db.add(expense_booking)
    
    db.commit()
    return RedirectResponse(f"/rechnungsliste", status_code=303)


@router.get("/receipt/{filename}")
def download_receipt(filename: str):
    """Download a receipt file."""
    receipt_path = os.path.join(BASE_DIR, "receipts", filename)
    
    if not os.path.exists(receipt_path):
        return HTMLResponse("Receipt file not found", status_code=404)
    
    return FileResponse(
        path=receipt_path,
        filename=filename
    )


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
