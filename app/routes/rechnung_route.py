"""Invoice generation, PDF creation and billing management routes."""

from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from app.utils.template_utils import create_templates
from sqlalchemy.orm import Session, joinedload
from database.db import get_db
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


from weasyprint import HTML
import datetime
import os
import secrets
from pathlib import Path
import base64
from config import config


router = APIRouter()
templates = create_templates()


# Add JSON filter to Jinja2
def from_json(value):
    if value:
        try:
            import json
            return json.loads(value)
        except (ValueError, TypeError):
            return []
    return []

templates.env.filters['from_json'] = from_json

# File security validation
ALLOWED_FILE_TYPES = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.tiff', '.bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file_upload(file) -> tuple[bool, str]:
    """Validate uploaded file for security and constraints."""
    if not file or not hasattr(file, 'filename') or not file.filename:
        return False, "Keine Datei ausgewählt"
    
    # Check file extension
    file_extension = os.path.splitext(file.filename.lower())[1]
    if file_extension not in ALLOWED_FILE_TYPES:
        return False, f"Dateityp nicht erlaubt. Erlaubte Typen: {', '.join(ALLOWED_FILE_TYPES)}"
    
    # Read file to check size and basic content validation
    file_content = file.file.read()
    file.file.seek(0)  # Reset file pointer
    
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        return False, f"Datei zu groß. Maximum: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Basic content validation for images
    if file_extension in {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.bmp'}:
        # Check if file starts with expected magic bytes
        if file_extension in {'.jpg', '.jpeg'} and not file_content.startswith(b'\xff\xd8'):
            return False, "Ungültiges JPEG-Format"
        elif file_extension == '.png' and not file_content.startswith(b'\x89PNG'):
            return False, "Ungültiges PNG-Format"
        elif file_extension == '.gif' and not file_content.startswith(b'GIF8'):
            return False, "Ungültiges GIF-Format"
    
    # Basic content validation for PDF
    elif file_extension == '.pdf' and not file_content.startswith(b'%PDF'):
        return False, "Ungültiges PDF-Format"
    
    return True, "OK"

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
    rechnungsdatum: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validate and parse the invoice date
    from app.utils.form_validation import FormValidator
    is_valid, error_msg = FormValidator.validate_date(rechnungsdatum, "Rechnungsdatum", allow_future=True)
    if not is_valid:
        return HTMLResponse(f"Fehler bei der Rechnungserstellung: {error_msg}", status_code=400)

    try:
        parsed_rechnungsdatum = datetime.datetime.strptime(rechnungsdatum, "%Y-%m-%d").date()
    except ValueError:
        return HTMLResponse("Fehler: Ungültiges Rechnungsdatum", status_code=400)
    
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

    if existierende_rechnung:
        # Rechnung existiert bereits - Warnung anzeigen und Erstellung verhindern
        status_text = "bezahlt" if existierende_rechnung.bezahlt else "unbezahlt"
        error_message = f"""
        <div style="max-width: 600px; margin: 2rem auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <div style="background: #fee; border: 1px solid #fcc; padding: 1.5rem; border-radius: 4px; margin-bottom: 1rem;">
                <h3 style="color: #d63384; margin: 0 0 1rem 0;">⚠️ Rechnung bereits vorhanden</h3>
                <p style="margin-bottom: 1rem; line-height: 1.6;">
                    Für den Auftrag <strong>#{auftrag_id}</strong> existiert bereits eine Rechnung
                    (Rechnung #{existierende_rechnung.id}, Status: <strong>{status_text}</strong>).
                </p>
                <p style="margin-bottom: 1rem; line-height: 1.6;">
                    Um eine neue Rechnung zu erstellen, müssen Sie zuerst die bestehende Rechnung löschen.
                </p>
            </div>
            <div style="text-align: center; gap: 1rem; display: flex; justify-content: center; flex-wrap: wrap;">
                <a href="/rechnungsliste" style="display: inline-block; padding: 0.75rem 1.5rem; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-weight: 500;">
                    → Zur Rechnungsübersicht
                </a>
                <a href="/rechnung" style="display: inline-block; padding: 0.75rem 1.5rem; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; font-weight: 500;">
                    ← Zurück zum Formular
                </a>
            </div>
        </div>
        """
        return HTMLResponse(content=error_message, status_code=400)

    # Summen berechnen (nur wenn keine existierende Rechnung vorhanden)
    gesamt_arbeit = 0
    for k in komponenten:
        if k.berechnungsbasis == "stunden":
            gesamt_arbeit += (k.anzahl_stunden or 0) * (k.stundenlohn or 0)
        elif k.berechnungsbasis == "quadratmeter":
            gesamt_arbeit += (k.anzahl_quadrat or 0) * (k.preis_pro_quadrat or 0)
    gesamt_material = sum(
        (m.preis_pro_einheit or 0) * (m.anzahl or 1)
        for m in materialien
    )

    faelligkeit = datetime.date.today() + datetime.timedelta(days=30)

    # Neue Rechnung anlegen
    neue_rechnung = Rechnung(
        kunde_id=kunde.id,
        auftrag_id=auftrag.id,
        unternehmensdaten_id=1,  # Anpassen falls mehrere Unternehmen
        rechnungsdatum=parsed_rechnungsdatum,
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
    with open(config.STATIC_DIR / "logo.png", "rb") as img_file:
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
    config.ensure_directories()

    # PDF-Datei erstellen (nach Rechnungs-ID benannt)
    pdf_path = config.INVOICES_DIR / f"Rechnung_{neue_rechnung.id}.pdf"

    try:
        HTML(string=rendered_html).write_pdf(str(pdf_path))
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
    # Get counts for each category
    alle_count = db.query(Rechnung).count()
    offene_count = db.query(Rechnung).filter(Rechnung.bezahlt == false()).count()
    bezahlte_count = db.query(Rechnung).filter(Rechnung.bezahlt == true()).count()
    
    # Filter rechnungen based on status
    query = db.query(Rechnung)
    if status == "offen":
        query = query.filter(Rechnung.bezahlt == false())
    elif status == "bezahlt":
        query = query.filter(Rechnung.bezahlt == true())

    rechnungen = query.order_by(Rechnung.id.desc()).all()
    
    # Get manual entries (bookings not linked to invoices) only for "alle rechnungen" tab
    manual_entries = []
    if status is None:  # Only show manual entries in "alle rechnungen" tab
        manual_entries = db.query(EinnahmeAusgabe).filter(
            EinnahmeAusgabe.rechnung_id.is_(None)
        ).order_by(EinnahmeAusgabe.datum.desc()).all()

    return templates.TemplateResponse(
        "rechnung_liste.html",
        {
            "request": request,
            "rechnungen": rechnungen,
            "status": status,
            "alle_count": alle_count,
            "offene_count": offene_count,
            "bezahlte_count": bezahlte_count,
            "manual_entries": manual_entries
        }
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
    
    # Get the cost date from form
    cost_date_str = form_data.get("cost_date")
    if cost_date_str:
        try:
            cost_date = datetime.datetime.strptime(cost_date_str, "%Y-%m-%d").date()
        except ValueError:
            cost_date = rechnung.rechnungsdatum if rechnung.rechnungsdatum else date.today()
    else:
        cost_date = rechnung.rechnungsdatum if rechnung.rechnungsdatum else date.today()
    
    # Create receipts directory if it doesn't exist
    config.ensure_directories()
    
    # Get Materialkosten category
    materialkosten_kategorie = db.query(EurKategorie).filter_by(
        name="Materialkosten", typ="ausgabe"
    ).first()
    
    # Process each material component
    materialien = db.query(MaterialKomponente).filter(
        MaterialKomponente.auftrag_id == rechnung.auftrag_id
    ).all()
    
    # Check if any actual costs are being provided to determine if we should update expenses
    any_costs_provided = False
    from decimal import Decimal
    total_expenses = Decimal('0.00')
    
    # First pass: Handle file uploads separately from cost/expense logic
    for material in materialien:
        receipt_key = f"receipt_{material.id}"
        receipt_files = form_data.getlist(receipt_key)
        
        # Handle multiple file uploads independently of cost updates
        # Filter out truly empty files (files with no name and no content)
        valid_files = []
        if receipt_files:
            for f in receipt_files:
                if hasattr(f, 'filename') and f.filename and f.filename.strip():
                    # Additional check: ensure file has content
                    if hasattr(f, 'file'):
                        try:
                            # Check if file has content by reading a small portion and resetting
                            current_pos = f.file.tell()
                            content_check = f.file.read(1)
                            f.file.seek(current_pos)
                            if content_check:  # File has content
                                valid_files.append(f)
                        except:
                            # If we can't check content, assume it's valid if it has a filename
                            valid_files.append(f)
                    else:
                        # If no file attribute, assume valid if it has filename
                        valid_files.append(f)
        
        if valid_files:
            # Initialize with existing files (preserve them)
            saved_filenames = []
            if material.receipt_path:
                existing_filenames = [f.strip() for f in material.receipt_path.split(',') if f.strip()]
                saved_filenames.extend(existing_filenames)
            
            # Process each uploaded file
            for i, receipt_file in enumerate(valid_files):
                # Validate file upload security
                is_valid, error_message = validate_file_upload(receipt_file)
                if not is_valid:
                    return HTMLResponse(f"Datei-Upload fehlgeschlagen für {material.bezeichnung} (Datei {i+1}): {error_message}", status_code=400)
                
                # Create safe filename with proper indexing (considering existing files)
                file_extension = os.path.splitext(receipt_file.filename.lower())[1]
                total_existing_files = len(saved_filenames)
                file_index = total_existing_files + i + 1
                safe_filename = f"material_{rechnung_id}_{material.id}_{file_index}_{secrets.token_hex(6)}{file_extension}"
                
                file_path = config.RECEIPTS_DIR / safe_filename
                
                # Save file
                try:
                    with open(file_path, "wb") as buffer:
                        content = await receipt_file.read()
                        buffer.write(content)
                    
                    saved_filenames.append(safe_filename)
                except Exception as e:
                    return HTMLResponse(f"Fehler beim Speichern der Datei für {material.bezeichnung} (Datei {i+1}): {str(e)}", status_code=500)
            
            # Only update the database if we actually processed files
            if saved_filenames:
                material.receipt_path = ','.join(saved_filenames)
    
    # Second pass: Check if any costs are provided
    for material in materialien:
        actual_cost_key = f"actual_cost_{material.id}"
        actual_cost = form_data.get(actual_cost_key)
        
        if actual_cost and float(actual_cost) > 0:
            any_costs_provided = True
            break
    
    # Only update expenses if costs are actually provided
    if any_costs_provided:
        # Delete existing expense bookings for this invoice's materials
        existing_expense_bookings = db.query(EinnahmeAusgabe).filter(
            EinnahmeAusgabe.rechnung_id == rechnung_id,
            EinnahmeAusgabe.typ == "ausgabe",
            EinnahmeAusgabe.kategorie_id == materialkosten_kategorie.id if materialkosten_kategorie else None
        ).all()
        
        for booking in existing_expense_bookings:
            db.delete(booking)
        
        # Third pass: Update costs and create expense bookings
        for material in materialien:
            actual_cost_key = f"actual_cost_{material.id}"
            actual_cost = form_data.get(actual_cost_key)

            if actual_cost and actual_cost.strip():
                # Validate material cost input
                from app.utils.form_validation import FormValidator
                is_valid, error_msg = FormValidator.validate_positive_number(
                    actual_cost, f"Materialkosten für {material.bezeichnung}", allow_zero=True)

                if not is_valid:
                    return HTMLResponse(f"Fehler: {error_msg}", status_code=400)

                from decimal import Decimal
                actual_cost_decimal = Decimal(actual_cost.replace(',', '.'))
                if actual_cost_decimal > 0:
                    total_expenses += actual_cost_decimal

                # Update material component with actual cost
                material.actual_cost = actual_cost_decimal
                
                # Create expense booking using the user-specified cost date
                expense_booking = EinnahmeAusgabe(
                    datum=cost_date,
                    betrag=actual_cost_decimal,  # Use Decimal for precise amounts
                    typ="ausgabe",
                    kategorie_id=materialkosten_kategorie.id if materialkosten_kategorie else None,
                    beschreibung=f"Materialkosten {material.bezeichnung}",
                    rechnung_id=rechnung_id
                )
                db.add(expense_booking)
    
    db.commit()
    
    # Add a simple success message in the URL for debugging
    files_uploaded = sum(1 for material in materialien if material.receipt_path and ',' in material.receipt_path or material.receipt_path)
    return RedirectResponse(f"/rechnungsliste?upload_success=1&files={files_uploaded}", status_code=303)


@router.post("/rechnung/{rechnung_id}/materialkosten/delete-receipt")
async def delete_material_receipt(
    rechnung_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a specific material receipt file."""
    form_data = await request.form()
    material_id = int(form_data.get("material_id"))
    filename = form_data.get("filename")
    
    # Get the material component
    material = db.query(MaterialKomponente).filter(
        MaterialKomponente.id == material_id
    ).first()
    
    if not material:
        return HTMLResponse("Material nicht gefunden", status_code=404)
    
    # Handle comma-separated list of files
    if not material.receipt_path:
        return HTMLResponse("Keine Belege vorhanden", status_code=404)
    
    receipt_files = [f.strip() for f in material.receipt_path.split(',')]
    
    # Verify the filename exists in the list
    if filename not in receipt_files:
        return HTMLResponse("Datei stimmt nicht überein", status_code=400)
    
    # Delete the file from disk
    receipt_path = config.RECEIPTS_DIR / filename
    if receipt_path.exists():
        try:
            receipt_path.unlink()
        except Exception as e:
            return HTMLResponse(f"Fehler beim Löschen der Datei: {str(e)}", status_code=500)
    
    # Remove the file from the list and update database
    receipt_files.remove(filename)
    if receipt_files:
        material.receipt_path = ','.join(receipt_files)
    else:
        material.receipt_path = None
    
    db.commit()
    
    # Return JSON response for AJAX requests
    accept_header = request.headers.get('accept', '')
    if 'application/json' in accept_header or request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from fastapi.responses import JSONResponse
        return JSONResponse({"success": True, "message": f"Beleg {filename} wurde erfolgreich gelöscht"})
    
    # Fallback to redirect for non-AJAX requests
    return RedirectResponse(f"/rechnung/{rechnung_id}/materialkosten", status_code=303)


@router.get("/receipt/{filename}")
def download_receipt(filename: str, db: Session = Depends(get_db)):
    """Download a receipt file with security validation."""
    # Security check: prevent directory traversal attacks
    if '..' in filename or '/' in filename or '\\' in filename:
        return HTMLResponse("Ungültiger Dateiname", status_code=400)
    
    # Verify file exists in database (ensures it's a legitimate receipt)
    # Check if filename exists in any comma-separated receipt_path
    materials_with_receipts = db.query(MaterialKomponente).filter(
        MaterialKomponente.receipt_path.like(f'%{filename}%')
    ).all()
    
    material_with_receipt = None
    # Additional verification: ensure filename is actually in the comma-separated list
    for material in materials_with_receipts:
        if material.receipt_path:
            receipt_files = [f.strip() for f in material.receipt_path.split(',') if f.strip()]
            if filename in receipt_files:
                material_with_receipt = material
                break
    
    if not material_with_receipt:
        return HTMLResponse("Beleg nicht in der Datenbank gefunden", status_code=404)
    
    receipt_path = config.RECEIPTS_DIR / filename
    
    if not receipt_path.exists():
        return HTMLResponse("Beleg-Datei nicht auf der Festplatte gefunden", status_code=404)
    
    # Determine content type based on file extension
    file_extension = os.path.splitext(filename.lower())[1]
    content_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.tiff': 'image/tiff',
        '.bmp': 'image/bmp'
    }
    
    media_type = content_types.get(file_extension, 'application/octet-stream')
    
    return FileResponse(
        path=str(receipt_path),
        filename=filename,
        media_type=media_type
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
    pdf_path = config.INVOICES_DIR / pdf_filename
    
    if not pdf_path.exists():
        return HTMLResponse("PDF-Datei nicht gefunden", status_code=404)
    
    return FileResponse(
        path=str(pdf_path),
        filename=pdf_filename,
        media_type='application/pdf'
    )


@router.post("/rechnung/{rechnung_id}/loeschen")
def delete_rechnung(rechnung_id: int, db: Session = Depends(get_db)):
    """Delete an invoice and all related data."""
    rechnung = db.query(Rechnung).filter(Rechnung.id == rechnung_id).first()

    if not rechnung:
        return HTMLResponse("Rechnung nicht gefunden", status_code=404)

    try:
        # Delete all related EÜR bookings first (to maintain referential integrity)
        related_bookings = db.query(EinnahmeAusgabe).filter(
            EinnahmeAusgabe.rechnung_id == rechnung_id).all()
        for booking in related_bookings:
            db.delete(booking)

        # Delete material receipt files if the invoice has an associated order
        if rechnung.auftrag_id:
            from app.models.material_komponente import MaterialKomponente
            materialien = db.query(MaterialKomponente).filter(
                MaterialKomponente.auftrag_id == rechnung.auftrag_id
            ).all()

            for material in materialien:
                if material.receipt_path:
                    # Handle comma-separated receipt files
                    receipt_files = [f.strip() for f in material.receipt_path.split(',') if f.strip()]
                    for filename in receipt_files:
                        receipt_path = config.RECEIPTS_DIR / filename
                        if receipt_path.exists():
                            try:
                                receipt_path.unlink()
                            except Exception as e:
                                print(f"Warning: Could not delete receipt file {filename}: {str(e)}")

                    # Clear the receipt_path from database
                    material.receipt_path = None

                # Clear material cost data since invoice is being deleted
                material.actual_cost = None

        # Delete the invoice PDF file if it exists
        pdf_filename = f"Rechnung_{rechnung_id}.pdf"
        pdf_path = config.INVOICES_DIR / pdf_filename
        if pdf_path.exists():
            try:
                pdf_path.unlink()
            except Exception as e:
                print(f"Warning: Could not delete PDF file {pdf_filename}: {str(e)}")

        # Delete the invoice from database
        db.delete(rechnung)
        db.commit()

        return RedirectResponse("/rechnungsliste?deleted=success", status_code=303)

    except Exception as e:
        db.rollback()
        return HTMLResponse(f"Fehler beim Löschen der Rechnung: {str(e)}", status_code=500)
