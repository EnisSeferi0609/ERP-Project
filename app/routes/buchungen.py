"""EÜR bookings, income/expense tracking and German tax compliance routes."""

from fastapi import APIRouter, Request, Form, Depends, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from typing import Optional, List
import json
import hashlib
import time
import os
import subprocess
import tempfile
from weasyprint import HTML

from database.db import get_db
from app.models.einnahme_ausgabe import EinnahmeAusgabe
from app.models.eur_kategorie import EurKategorie
from app.models.rechnung import Rechnung
from app.models.unternehmensdaten import Unternehmensdaten
from app.utils.template_utils import create_templates
from app.utils.file_validation import validate_file_upload
from config import config

router = APIRouter()
templates = create_templates()

def save_receipt_file(file: UploadFile, booking_id: int) -> str:
    """Save uploaded file and return the filename."""
    # Generate unique filename
    import secrets
    file_extension = os.path.splitext(file.filename.lower())[1]
    unique_filename = f"booking_{booking_id}_{secrets.token_hex(6)}{file_extension}"
    
    # Ensure receipts directory exists
    config.ensure_directories()
    file_path = config.RECEIPTS_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    return unique_filename

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
    request: Request,
    betrag: str = Form(...),  # Changed to str for validation
    typ: str = Form(...),
    kategorie_id: str = Form(...),  # Changed to str for validation
    beschreibung: str = Form(""),
    redirect_to: str = Form("/euer"),
    receipt_files: List[UploadFile] = [],
    # Single booking fields
    datum: Optional[str] = Form(None),  # Changed to str for validation
    # Bulk booking fields
    bulk_mode: str = Form("false"),
    start_datum: Optional[str] = Form(None),  # Changed to str for validation
    end_datum: Optional[str] = Form(None),  # Changed to str for validation
    interval: str = Form("monthly"),
    db: Session = Depends(get_db)
):
    # Validate form data
    from app.utils.form_validation import FormValidator

    # Validate amount
    is_valid, error_msg = FormValidator.validate_positive_number(betrag, "Betrag")
    if not is_valid:
        kategorien = db.query(EurKategorie).order_by(EurKategorie.typ, EurKategorie.name).all()
        return templates.TemplateResponse("neue_buchung.html", {
            "request": request,
            "kategorien": kategorien,
            "error_message": f"Validierungsfehler: {error_msg}"
        })

    # Validate category
    try:
        kategorie_id_int = int(kategorie_id)
    except ValueError:
        kategorien = db.query(EurKategorie).order_by(EurKategorie.typ, EurKategorie.name).all()
        return templates.TemplateResponse("neue_buchung.html", {
            "request": request,
            "kategorien": kategorien,
            "error_message": "Validierungsfehler: Ungültige Kategorie ausgewählt"
        })

    # Convert validated amount to Decimal for precise calculations
    from decimal import Decimal
    betrag_decimal = Decimal(betrag.replace(',', '.'))

    # Validate dates and convert from strings
    booking_dates = []
    is_bulk_mode = bulk_mode.lower() == "true"

    if is_bulk_mode:
        # Validate bulk booking dates
        if not start_datum or not end_datum:
            kategorien = db.query(EurKategorie).order_by(EurKategorie.typ, EurKategorie.name).all()
            return templates.TemplateResponse("neue_buchung.html", {
                "request": request,
                "kategorien": kategorien,
                "error_message": "Start- und Enddatum sind erforderlich für Mehrfachbuchungen"
            })

        try:
            start_date = datetime.strptime(start_datum, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_datum, "%Y-%m-%d").date()
        except ValueError:
            kategorien = db.query(EurKategorie).order_by(EurKategorie.typ, EurKategorie.name).all()
            return templates.TemplateResponse("neue_buchung.html", {
                "request": request,
                "kategorien": kategorien,
                "error_message": "Ungültiges Datumsformat"
            })

        current_date = start_date
        while current_date <= end_date:
            booking_dates.append(current_date)

            # Calculate next date based on interval
            if interval == "monthly":
                current_date = current_date + relativedelta(months=1)
            elif interval == "quarterly":
                current_date = current_date + relativedelta(months=3)
            elif interval == "yearly":
                current_date = current_date + relativedelta(years=1)
            else:
                break  # Unknown interval
    else:
        # Validate single booking date
        if not datum:
            kategorien = db.query(EurKategorie).order_by(EurKategorie.typ, EurKategorie.name).all()
            return templates.TemplateResponse("neue_buchung.html", {
                "request": request,
                "kategorien": kategorien,
                "error_message": "Datum ist erforderlich"
            })

        try:
            single_date = datetime.strptime(datum, "%Y-%m-%d").date()
            booking_dates = [single_date]
        except ValueError:
            kategorien = db.query(EurKategorie).order_by(EurKategorie.typ, EurKategorie.name).all()
            return templates.TemplateResponse("neue_buchung.html", {
                "request": request,
                "kategorien": kategorien,
                "error_message": "Ungültiges Datumsformat"
            })

    # Create bookings for all dates
    created_bookings = []
    for booking_date in booking_dates:
        buchung = EinnahmeAusgabe(
            datum=booking_date,
            betrag=betrag_decimal,  # Use validated Decimal
            typ=typ.lower(),
            kategorie_id=kategorie_id_int,  # Use validated int
            beschreibung=beschreibung
        )
        db.add(buchung)
        db.commit()
        db.refresh(buchung)
        created_bookings.append(buchung)
    
    # Handle file uploads if any (attach to the first booking only)
    saved_files = []
    if receipt_files and created_bookings:
        first_booking = created_bookings[0]

        for file in receipt_files:
            # Skip empty files
            if not file or not file.filename:
                continue

            # Validate file
            is_valid, error_message = validate_file_upload(file)
            if not is_valid:
                # Delete all created bookings if file validation fails
                for booking in created_bookings:
                    db.delete(booking)
                db.commit()
                return HTMLResponse(
                    f"Fehler beim Datei-Upload: {error_message}",
                    status_code=400
                )

            # Save file
            try:
                filename = save_receipt_file(file, first_booking.id)
                saved_files.append(filename)
            except Exception as e:
                # Delete all bookings and any previously saved files
                for booking in created_bookings:
                    db.delete(booking)
                db.commit()

                # Clean up any files that were saved
                for saved_file in saved_files:
                    try:
                        (config.RECEIPTS_DIR / saved_file).unlink()
                    except:
                        pass

                return HTMLResponse(
                    f"Fehler beim Speichern der Datei: {str(e)}",
                    status_code=500
                )

        # Update first booking with file information
        if saved_files:
            first_booking.receipt_files = json.dumps(saved_files)
            db.commit()
    
    return RedirectResponse(redirect_to, status_code=303)


# Edit manual booking
@router.get("/buchungen/{booking_id}/bearbeiten", response_class=HTMLResponse)
def edit_manual_booking(booking_id: int, request: Request, db: Session = Depends(get_db)):
    buchung = db.query(EinnahmeAusgabe).filter(
        EinnahmeAusgabe.id == booking_id,
        EinnahmeAusgabe.rechnung_id.is_(None)  # Only manual bookings
    ).first()
    
    if not buchung:
        return HTMLResponse("Buchung nicht gefunden", status_code=404)
    
    kategorien = db.query(EurKategorie).order_by(
        EurKategorie.typ, EurKategorie.name).all()
    
    return templates.TemplateResponse("edit_manual_booking.html", {
        "request": request,
        "buchung": buchung,
        "kategorien": kategorien
    })


# Save edited manual booking
@router.post("/buchungen/{booking_id}/bearbeiten")
def save_manual_booking(
    booking_id: int,
    datum: date = Form(...),
    betrag: float = Form(...),
    typ: str = Form(...),
    kategorie_id: int = Form(...),
    beschreibung: str = Form(""),
    receipt_files: List[UploadFile] = [],
    db: Session = Depends(get_db)
):
    buchung = db.query(EinnahmeAusgabe).filter(
        EinnahmeAusgabe.id == booking_id,
        EinnahmeAusgabe.rechnung_id.is_(None)  # Only manual bookings
    ).first()
    
    if not buchung:
        return HTMLResponse("Buchung nicht gefunden", status_code=404)
    
    # Update booking data
    buchung.datum = datum
    buchung.betrag = betrag
    buchung.typ = typ.lower()
    buchung.kategorie_id = kategorie_id
    buchung.beschreibung = beschreibung
    
    # Handle file uploads if any
    existing_files = []
    if buchung.receipt_files:
        try:
            existing_files = json.loads(buchung.receipt_files)
        except:
            existing_files = []
    
    saved_files = existing_files.copy()  # Keep existing files
    
    if receipt_files:
        for file in receipt_files:
            # Skip empty files
            if not file or not file.filename:
                continue
                
            # Validate file
            is_valid, error_message = validate_file_upload(file)
            if not is_valid:
                return HTMLResponse(
                    f"Fehler beim Datei-Upload: {error_message}",
                    status_code=400
                )
            
            # Save file
            try:
                filename = save_receipt_file(file, buchung.id)
                saved_files.append(filename)
            except Exception as e:
                return HTMLResponse(
                    f"Fehler beim Speichern der Datei: {str(e)}",
                    status_code=500
                )
    
    # Update booking with file information
    if saved_files:
        buchung.receipt_files = json.dumps(saved_files)
    
    db.commit()
    
    return RedirectResponse("/rechnungsliste", status_code=303)


# Delete receipt file from manual booking
@router.post("/buchungen/{booking_id}/delete-receipt")
def delete_manual_booking_receipt(
    booking_id: int,
    filename: str = Form(...),
    db: Session = Depends(get_db)
):
    buchung = db.query(EinnahmeAusgabe).filter(
        EinnahmeAusgabe.id == booking_id,
        EinnahmeAusgabe.rechnung_id.is_(None)  # Only manual bookings
    ).first()
    
    if not buchung:
        return HTMLResponse("Buchung nicht gefunden", status_code=404)
    
    # Remove file from receipt_files
    if buchung.receipt_files:
        try:
            receipt_files = json.loads(buchung.receipt_files)
            if filename in receipt_files:
                receipt_files.remove(filename)
                
                # Delete physical file
                receipt_path = config.RECEIPTS_DIR / filename
                if receipt_path.exists():
                    receipt_path.unlink()
                
                # Update database
                if receipt_files:
                    buchung.receipt_files = json.dumps(receipt_files)
                else:
                    buchung.receipt_files = None
                
                db.commit()
                
                return HTMLResponse("OK", status_code=200)
        except Exception as e:
            return HTMLResponse(f"Fehler: {str(e)}", status_code=500)
    
    return HTMLResponse("Datei nicht gefunden", status_code=404)


# Delete manual booking completely
@router.post("/buchungen/{booking_id}/loeschen")
def delete_manual_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    buchung = db.query(EinnahmeAusgabe).filter(
        EinnahmeAusgabe.id == booking_id,
        EinnahmeAusgabe.rechnung_id.is_(None)  # Only manual bookings
    ).first()

    if not buchung:
        return HTMLResponse("Buchung nicht gefunden", status_code=404)

    # Delete associated receipt files from disk
    if buchung.receipt_files:
        try:
            receipt_files = json.loads(buchung.receipt_files)
            for filename in receipt_files:
                receipt_path = config.RECEIPTS_DIR / filename
                if receipt_path.exists():
                    try:
                        receipt_path.unlink()
                    except Exception as e:
                        # Log the error but continue with deletion
                        print(f"Warning: Could not delete receipt file {filename}: {str(e)}")
        except Exception as e:
            print(f"Warning: Could not parse receipt files for booking {booking_id}: {str(e)}")

    # Delete the booking from database
    db.delete(buchung)
    db.commit()

    return RedirectResponse("/rechnungsliste", status_code=303)


# Rechnung als bezahlt/unbezahlt markieren & Buchung erzeugen
@router.post("/rechnung/{rechnung_id}/status")
def rechnung_status_toggle(
    rechnung_id: int, 
    payment_date: Optional[str] = Form(None),
    status_filter: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    rechnung = db.query(Rechnung).filter(Rechnung.id == rechnung_id).first()
    if not rechnung:
        return HTMLResponse("Nicht gefunden", status_code=404)
    
    # Determine the action based on current state and whether payment_date is provided
    if not rechnung.bezahlt:  # Currently unpaid, trying to mark as paid
        # Check if invoice has materials that need cost tracking
        if rechnung.auftrag and rechnung.auftrag.materialien:
            # Check if all materials have actual costs entered
            materials_without_costs = [
                m for m in rechnung.auftrag.materialien 
                if m.actual_cost is None or m.actual_cost <= 0
            ]
            
            if materials_without_costs:
                # Block payment and redirect with error message
                redirect_url = f"/rechnungsliste?error=material_costs_missing&rechnung_id={rechnung_id}"
                if status_filter:
                    redirect_url += f"&status={status_filter}"
                return RedirectResponse(redirect_url, status_code=303)
        
        # Mark as paid
        rechnung.bezahlt = True
        
    elif rechnung.bezahlt and payment_date:  # Currently paid, and new payment date provided
        # Delete existing invoice-related bookings to recreate with new date
        existing_invoice_bookings = db.query(EinnahmeAusgabe).filter_by(
            rechnung_id=rechnung.id).all()
        for buchung in existing_invoice_bookings:
            db.delete(buchung)
        # Keep as paid, will update payment date below
        
    else:  # Currently paid, no payment date provided (toggle to unpaid)
        # Delete ALL invoice-related bookings (both income and any automatic bookings)
        # This ensures complete cleanup when marking invoice as unpaid
        all_invoice_bookings = db.query(EinnahmeAusgabe).filter_by(
            rechnung_id=rechnung.id).all()
        for buchung in all_invoice_bookings:
            db.delete(buchung)
        rechnung.bezahlt = False
    
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
            # Separate Buchung für each material
            for mk in rechnung.auftrag.materialien:
                material_betrag = mk.anzahl * mk.preis_pro_einheit
                if material_betrag > 0 and material_erloese_kategorie:
                    material_desc = f"Materialerlöse {mk.bezeichnung}" if mk.bezeichnung else "Materialerlöse"
                    
                    material_buchung = EinnahmeAusgabe(
                        datum=booking_date,
                        betrag=material_betrag,
                        typ="einnahme",
                        kategorie_id=material_erloese_kategorie.id,
                        beschreibung=material_desc,
                        rechnung_id=rechnung.id
                    )
                    db.add(material_buchung)
            
            # Separate Buchung für Arbeitserlöse
            arbeits_summe = 0
            work_descriptions = []
            for ak in rechnung.auftrag.arbeit_komponenten:
                if ak.berechnungsbasis == "stunden":
                    arbeits_summe += (ak.anzahl_stunden or 0) * (ak.stundenlohn or 0)
                    if ak.beschreibung:
                        work_descriptions.append(f"{ak.beschreibung} ({ak.anzahl_stunden}h)")
                elif ak.berechnungsbasis == "quadratmeter":
                    arbeits_summe += (ak.anzahl_quadrat or 0) * (ak.preis_pro_quadrat or 0)
                    if ak.beschreibung:
                        work_descriptions.append(f"{ak.beschreibung} ({ak.anzahl_quadrat}m²)")
                        
            if arbeits_summe > 0 and erloese_kategorie:
                # Create description with work details
                if work_descriptions:
                    arbeits_desc = f"Arbeitserlöse ({', '.join(work_descriptions)})"
                else:
                    arbeits_desc = "Arbeitserlöse"
                    
                arbeits_buchung = EinnahmeAusgabe(
                    datum=booking_date,
                    betrag=arbeits_summe,
                    typ="einnahme",
                    kategorie_id=erloese_kategorie.id,
                    beschreibung=arbeits_desc,
                    rechnung_id=rechnung.id
                )
                db.add(arbeits_buchung)
        
        db.commit()

    # Preserve the filter when redirecting back
    redirect_url = "/rechnungsliste"
    if status_filter:
        redirect_url += f"?status={status_filter}"
    return RedirectResponse(redirect_url, status_code=303)


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

    # Calculate reports data for all years (for reports view)
    reports_data = {}
    if view == 'reports':
        for report_year in available_years:
            year_entries = db.query(EinnahmeAusgabe).filter(
                func.strftime('%Y', EinnahmeAusgabe.datum) == str(report_year)
            ).all()

            year_einnahmen = sum(e.betrag for e in year_entries if e.typ.lower() == "einnahme")
            year_ausgaben = sum(e.betrag for e in year_entries if e.typ.lower() == "ausgabe")
            year_saldo = year_einnahmen - year_ausgaben

            reports_data[report_year] = {
                'einnahmen': year_einnahmen,
                'ausgaben': year_ausgaben,
                'saldo': year_saldo
            }
    
    # Filter entries by year and order chronologically (oldest first)
    eintraege = db.query(EinnahmeAusgabe).filter(
        func.strftime('%Y', EinnahmeAusgabe.datum) == str(year)
    ).order_by(EinnahmeAusgabe.datum.asc()).all()

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
    
    # Create a mixed timeline with invoices and manual entries sorted by date
    timeline_items = []
    
    # Add invoice groups to timeline
    for rechnung_id, group in grouped_entries.items():
        timeline_items.append({
            'type': 'invoice_group',
            'rechnung_id': rechnung_id,
            'data': group
        })

    # Add manual entries to timeline
    for entry in manual_entries:
        timeline_items.append({
            'type': 'manual_entry',
            'date': entry.datum,
            'data': entry
        })

    # Sort timeline: invoices by ID (highest first), manual entries by date (newest first)
    timeline_items.sort(key=lambda x: (
        x['type'] == 'manual_entry',  # Manual entries come after invoices
        -x['rechnung_id'] if x['type'] == 'invoice_group' else -x['date'].toordinal()
    ))

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
        "current_year": date.today().year,
        "available_years": available_years,
        "eintraege": eintraege,
        "grouped_entries": grouped_entries,
        "manual_entries": manual_entries,
        "timeline_items": timeline_items,
        "einnahmen_summe": einnahmen_summe,
        "ausgaben_summe": ausgaben_summe,
        "saldo": saldo,
        "labels": labels,
        "daten_einnahmen": daten_einnahmen,
        "daten_ausgaben": daten_ausgaben,
        "reports_data": reports_data
    })


@router.get("/euer/{year}/pdf")
def generate_eur_pdf(year: int, db: Session = Depends(get_db)):
    """Generate EÜR PDF report for a specific year"""

    # Get company data
    company_data = db.query(Unternehmensdaten).first()
    if not company_data:
        return HTMLResponse("Unternehmensdaten nicht gefunden", status_code=404)

    # Get all entries for the year
    entries = db.query(EinnahmeAusgabe).filter(
        func.strftime('%Y', EinnahmeAusgabe.datum) == str(year)
    ).order_by(EinnahmeAusgabe.datum.asc()).all()

    if not entries:
        return HTMLResponse(f"Keine Buchungen für das Jahr {year} gefunden", status_code=404)

    # Calculate totals
    total_income = sum(e.betrag for e in entries if e.typ.lower() == "einnahme")
    total_expenses = sum(e.betrag for e in entries if e.typ.lower() == "ausgabe")
    profit = total_income - total_expenses

    # Group entries by category
    income_categories = defaultdict(list)
    expense_categories = defaultdict(list)

    for entry in entries:
        if entry.typ.lower() == "einnahme":
            category_name = entry.kategorie.name if entry.kategorie else "Sonstige Einnahmen"
            income_categories[category_name].append(entry)
        else:
            category_name = entry.kategorie.name if entry.kategorie else "Sonstige Ausgaben"
            expense_categories[category_name].append(entry)

    # Create monthly summary
    monthly_data = {}
    for entry in entries:
        month_key = entry.datum.strftime('%m/%Y')
        if month_key not in monthly_data:
            monthly_data[month_key] = {'income': 0, 'expenses': 0, 'balance': 0}

        if entry.typ.lower() == "einnahme":
            monthly_data[month_key]['income'] += entry.betrag
        else:
            monthly_data[month_key]['expenses'] += entry.betrag

        monthly_data[month_key]['balance'] = (
            monthly_data[month_key]['income'] - monthly_data[month_key]['expenses']
        )

    # Sort monthly data
    monthly_data = dict(sorted(monthly_data.items()))

    # Render HTML template
    rendered_html = templates.get_template("eur_pdf_template.html").render({
        "year": year,
        "creation_date": date.today(),
        "company_data": company_data,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "profit": profit,
        "income_categories": dict(income_categories),
        "expense_categories": dict(expense_categories),
        "monthly_data": monthly_data
    })

    # Generate PDF using WeasyPrint
    try:
        # Generate PDF directly from HTML string
        pdf_content = HTML(string=rendered_html).write_pdf()

        return Response(
            content=pdf_content,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="EÜR_{year}_{company_data.unternehmen_name.replace(" ", "_")}.pdf"'
            }
        )

    except Exception as e:
        return HTMLResponse(f"Fehler bei der PDF-Generierung: {str(e)}", status_code=500)
