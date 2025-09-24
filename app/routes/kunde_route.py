"""Customer management API routes and endpoints."""

from sqlalchemy.orm import joinedload, Session
from app.models.material_komponente import MaterialKomponente
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.rechnung import Rechnung
from app.models.einnahme_ausgabe import EinnahmeAusgabe
from typing import Optional
import datetime
from app.models.kunde import Kunde
from database.db import get_db
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from app.utils.template_utils import create_templates


router = APIRouter()
templates = create_templates()




@router.get("/kunde", response_class=HTMLResponse)
def formular_anzeigen(request: Request, db: Session = Depends(get_db)):
    """Display customer form with list of existing customers."""
    kunden = db.query(Kunde).all()
    return templates.TemplateResponse("formular_kunde.html", {
        "request": request,
        "kunden": kunden
    })


@router.get("/kundenliste", response_class=HTMLResponse)
def kunden_liste(request: Request, db: Session = Depends(get_db)):
    """Display customer list with orders and invoice status."""
    # Use efficient join query to avoid N+1 problem
    from sqlalchemy.orm import selectinload
    
    # Load customers with their orders and invoices in optimized queries
    kunden = db.query(Kunde).options(
        selectinload(Kunde.auftraege)
    ).order_by(Kunde.id.desc()).all()
    
    # Get all auftrag IDs to fetch invoices efficiently
    auftrag_ids = [auftrag.id for kunde in kunden for auftrag in kunde.auftraege]
    
    # Fetch all invoices for these orders in a single query
    rechnungen_dict = {}
    if auftrag_ids:
        rechnungen = db.query(Rechnung).filter(Rechnung.auftrag_id.in_(auftrag_ids)).all()
        rechnungen_dict = {r.auftrag_id: r for r in rechnungen}
    
    # Add invoice status for each Auftrag (using pre-loaded data)
    for kunde in kunden:
        for auftrag in kunde.auftraege:
            rechnung = rechnungen_dict.get(auftrag.id)
            if rechnung:
                auftrag.invoice_status = "bezahlt" if rechnung.bezahlt else "offen"
            else:
                auftrag.invoice_status = "keine Rechnung"
    
    return templates.TemplateResponse(
        "kunden_liste.html", {
            "request": request, "kunden": kunden})


@router.post("/kunden")
def kunde_speichern(
    request: Request,
    bestehend: Optional[str] = Form(None),
    kunde_id: Optional[str] = Form(None),  # Als str einlesen!
    kundenart: Optional[str] = Form(None),
    kunde_firmenname: Optional[str] = Form(None),
    kunde_gesellschaftsform: Optional[str] = Form(None),
    ansprechpartner_vorname: Optional[str] = Form(None),
    ansprechpartner_nachname: Optional[str] = Form(None),
    kunde_vorname: Optional[str] = Form(None),
    kunde_nachname: Optional[str] = Form(None),
    kunde_rechnungsadresse: Optional[str] = Form(None),
    kunde_rechnung_plz: Optional[str] = Form(None),
    kunde_rechnung_ort: Optional[str] = Form(None),
    kunde_email: Optional[str] = Form(None),
    kunde_telefon: Optional[str] = Form(None),
    notizen: Optional[str] = Form(None),
    kunde_seit: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Save new customer or update existing customer data."""
    # Validate form data
    from app.utils.form_validation import validate_customer_form

    form_data = {
        'kundenart': kundenart or '',
        'kunde_firmenname': kunde_firmenname or '',
        'ansprechpartner_vorname': ansprechpartner_vorname or '',
        'ansprechpartner_nachname': ansprechpartner_nachname or '',
        'kunde_vorname': kunde_vorname or '',
        'kunde_nachname': kunde_nachname or '',
        'kunde_email': kunde_email or '',
        'kunde_telefon': kunde_telefon or '',
        'kunde_rechnungsadresse': kunde_rechnungsadresse or '',
        'kunde_rechnung_plz': kunde_rechnung_plz or '',
        'kunde_rechnung_ort': kunde_rechnung_ort or ''
    }

    validation_errors = validate_customer_form(form_data)
    if validation_errors:
        # Return form with validation errors
        kunden = db.query(Kunde).all()
        error_message = "Bitte korrigieren Sie folgende Fehler:<br>" + "<br>".join(validation_errors)
        return templates.TemplateResponse("formular_kunde.html", {
            "request": request,
            "kunden": kunden,
            "error_message": error_message,
            "form_data": form_data  # Pass back form data to preserve user input
        })
    if bestehend == "ja":
        if not kunde_id:
            raise HTTPException(status_code=400,
                                detail="Kein bestehender Kunde ausgewählt.")
        try:
            kunde_id = int(kunde_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Ungültige Kunden-ID.")

        kunde = db.query(Kunde).filter(Kunde.id == kunde_id).first()
        if not kunde:
            raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

        # Felder aktualisieren
        kunde.kundenart = kundenart
        kunde.kunde_email = kunde_email
        kunde.kunde_telefon = kunde_telefon
        kunde.kunde_rechnungsadresse = kunde_rechnungsadresse
        kunde.kunde_rechnung_plz = kunde_rechnung_plz
        kunde.kunde_rechnung_ort = kunde_rechnung_ort
        kunde.notizen = notizen
        
        # Update kunde_seit if provided
        if kunde_seit:
            try:
                kunde.kunde_seit = datetime.datetime.strptime(kunde_seit, '%Y-%m-%d').date()
            except ValueError:
                pass  # Keep existing date if invalid format

        if kundenart == "Gewerbekunde":
            kunde.kunde_firmenname = kunde_firmenname
            kunde.kunde_gesellschaftsform = kunde_gesellschaftsform
            kunde.ansprechpartner_vorname = ansprechpartner_vorname
            kunde.ansprechpartner_nachname = ansprechpartner_nachname
            kunde.kunde_vorname = None
            kunde.kunde_nachname = None
        elif kundenart == "Privatkunde":
            kunde.kunde_vorname = kunde_vorname
            kunde.kunde_nachname = kunde_nachname
            kunde.kunde_firmenname = None
            kunde.kunde_gesellschaftsform = None
            kunde.ansprechpartner_vorname = None
            kunde.ansprechpartner_nachname = None

        db.commit()

    else:
        # Parse kunde_seit - now required
        if not kunde_seit:
            raise HTTPException(status_code=400, detail="Bitte geben Sie ein 'Kunde seit' Datum ein oder klicken Sie auf 'Heutiges Datum'")
        
        try:
            kunde_seit_date = datetime.datetime.strptime(kunde_seit, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Ungültiges Datum format")
        
        neuer_kunde = Kunde(
            kundenart=kundenart,
            kunde_firmenname=(
                kunde_firmenname if kundenart == "Gewerbekunde" else None
            ),
            kunde_gesellschaftsform=(
                kunde_gesellschaftsform
                if kundenart == "Gewerbekunde" else None
            ),
            ansprechpartner_vorname=(
                ansprechpartner_vorname
                if kundenart == "Gewerbekunde" else None
            ),
            ansprechpartner_nachname=(
                ansprechpartner_nachname
                if kundenart == "Gewerbekunde" else None
            ),
            kunde_vorname=(
                kunde_vorname if kundenart == "Privatkunde" else None
            ),
            kunde_nachname=(
                kunde_nachname if kundenart == "Privatkunde" else None
            ),
            kunde_rechnungsadresse=kunde_rechnungsadresse,
            kunde_rechnung_plz=kunde_rechnung_plz,
            kunde_rechnung_ort=kunde_rechnung_ort,
            kunde_email=kunde_email,
            kunde_telefon=kunde_telefon,
            notizen=notizen,
            kunde_seit=kunde_seit_date)
        db.add(neuer_kunde)
        db.commit()

    return RedirectResponse("/kunde", status_code=303)


@router.get("/api/kunde/{kunde_id}")
def get_kunde_data(kunde_id: int, db: Session = Depends(get_db)):
    kunde = db.query(Kunde).filter(Kunde.id == kunde_id).first()
    if not kunde:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    return {
        "kundenart": kunde.kundenart,
        "kunde_firmenname": kunde.kunde_firmenname,
        "kunde_gesellschaftsform": kunde.kunde_gesellschaftsform,
        "ansprechpartner_vorname": kunde.ansprechpartner_vorname,
        "ansprechpartner_nachname": kunde.ansprechpartner_nachname,
        "kunde_vorname": kunde.kunde_vorname,
        "kunde_nachname": kunde.kunde_nachname,
        "kunde_rechnungsadresse": kunde.kunde_rechnungsadresse,
        "kunde_rechnung_plz": kunde.kunde_rechnung_plz,
        "kunde_rechnung_ort": kunde.kunde_rechnung_ort,
        "kunde_email": kunde.kunde_email,
        "kunde_telefon": kunde.kunde_telefon,
        "notizen": kunde.notizen,
        "kunde_seit": kunde.kunde_seit.isoformat() if kunde.kunde_seit else None
    }


@router.post("/kunde/loeschen/{kunde_id}")
def kunde_loeschen(kunde_id: int, db: Session = Depends(get_db)):
    kunde = db.query(Kunde).filter(Kunde.id == kunde_id).first()
    if not kunde:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    # Delete all aufträge and their related data for this customer
    for auftrag in kunde.auftraege:
        # First, delete EÜR entries for all invoices of this auftrag
        rechnungen = db.query(Rechnung).filter(Rechnung.auftrag_id == auftrag.id).all()
        for rechnung in rechnungen:
            # Delete all EÜR entries for each invoice
            db.query(EinnahmeAusgabe).filter(EinnahmeAusgabe.rechnung_id == rechnung.id).delete()

            # Delete invoice PDF file(s) - handle both old and new filename formats
            from config import config
            import re

            # Create safe customer name for filename
            if kunde.kundenart == "Privatkunde":
                customer_name = f"{kunde.kunde_nachname}_{kunde.kunde_vorname}"
            else:
                customer_name = f"{kunde.ansprechpartner_nachname}_{kunde.ansprechpartner_vorname}"

            # Remove special characters for filename
            safe_customer_name = re.sub(r'[^a-zA-Z0-9_-]', '', customer_name)

            # Try to delete both possible filename formats
            possible_filenames = [
                f"Rechnung_{rechnung.id}_{safe_customer_name}.pdf",  # New format
                f"Rechnung_{rechnung.id}.pdf"  # Old format
            ]

            for pdf_filename in possible_filenames:
                pdf_path = config.INVOICES_DIR / pdf_filename
                if pdf_path.exists():
                    try:
                        pdf_path.unlink()
                        print(f"Deleted PDF file: {pdf_filename}")
                    except Exception as e:
                        print(f"Warning: Could not delete PDF file {pdf_filename}: {str(e)}")

        # Delete material receipt files before deleting components
        materialien = db.query(MaterialKomponente).filter(
            MaterialKomponente.auftrag_id == auftrag.id).all()
        for material in materialien:
            if material.receipt_path:
                from config import config
                # Handle comma-separated receipt files
                receipt_files = [f.strip() for f in material.receipt_path.split(',') if f.strip()]
                for filename in receipt_files:
                    receipt_path = config.RECEIPTS_DIR / filename
                    if receipt_path.exists():
                        try:
                            receipt_path.unlink()
                        except Exception as e:
                            print(f"Warning: Could not delete receipt file {filename}: {str(e)}")

        # Then delete invoices
        db.query(Rechnung).filter(Rechnung.auftrag_id == auftrag.id).delete()

        # Delete work and material components
        db.query(ArbeitKomponente).filter(
            ArbeitKomponente.auftrag_id == auftrag.id).delete()
        db.query(MaterialKomponente).filter(
            MaterialKomponente.auftrag_id == auftrag.id).delete()

        # Delete the auftrag itself
        db.delete(auftrag)

    # Dann den Kunden löschen
    db.delete(kunde)
    db.commit()

    return RedirectResponse(url="/kundenliste", status_code=303)


@router.get("/api/auftrag/{auftrag_id}")
def get_auftrag_details(auftrag_id: int, db: Session = Depends(get_db)):
    """Get detailed auftrag information including components and invoice status."""
    from app.models.auftrag import Auftrag

    auftrag = db.query(Auftrag).options(
        joinedload(Auftrag.arbeit_komponenten),
        joinedload(Auftrag.materialien)
    ).filter(Auftrag.id == auftrag_id).first()

    if not auftrag:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")

    # Check if invoice exists for this auftrag
    rechnung = db.query(Rechnung).filter(Rechnung.auftrag_id == auftrag_id).first()
    has_invoice = rechnung is not None

    # Determine invoice status
    if rechnung:
        invoice_status = "bezahlt" if rechnung.bezahlt else "offen"
    else:
        invoice_status = "keine Rechnung"

    return {
        "id": auftrag.id,
        "beschreibung": auftrag.beschreibung,
        "auftrag_start": auftrag.auftrag_start.isoformat() if auftrag.auftrag_start else None,
        "rechnungsstatus": invoice_status,
        "kunde_leistungsadresse": auftrag.kunde_leistungsadresse,
        "kunde_leistung_plz": auftrag.kunde_leistung_plz,
        "kunde_leistung_ort": auftrag.kunde_leistung_ort,
        "has_invoice": has_invoice,
        "arbeit_komponenten": [
            {
                "id": ak.id,
                "arbeit": ak.arbeit,
                "beschreibung": ak.beschreibung,
                "komponente_start": ak.komponente_start.isoformat() if ak.komponente_start else None,
                "komponente_ende": ak.komponente_ende.isoformat() if ak.komponente_ende else None,
                "berechnungsbasis": ak.berechnungsbasis,
                "anzahl_stunden": ak.anzahl_stunden,
                "stundenlohn": ak.stundenlohn,
                "anzahl_quadrat": ak.anzahl_quadrat,
                "preis_pro_quadrat": ak.preis_pro_quadrat
            }
            for ak in auftrag.arbeit_komponenten
        ],
        "materialien": [
            {
                "id": mk.id,
                "bezeichnung": mk.bezeichnung,
                "berechnungseinheit": mk.berechnungseinheit,
                "anzahl": mk.anzahl,
                "preis_pro_einheit": mk.preis_pro_einheit
            }
            for mk in auftrag.materialien
        ]
    }


@router.post("/api/auftrag/{auftrag_id}")
def update_auftrag(
    auftrag_id: int,
    beschreibung: str = Form(...),
    auftrag_start: Optional[str] = Form(None),
    kunde_leistungsadresse: Optional[str] = Form(None),
    kunde_leistung_plz: Optional[str] = Form(None),
    kunde_leistung_ort: Optional[str] = Form(None),
    arbeitskomponenten: Optional[str] = Form(None),
    materialkomponenten: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update auftrag details (only if no invoice exists)."""
    from app.models.auftrag import Auftrag

    auftrag = db.query(Auftrag).filter(Auftrag.id == auftrag_id).first()
    if not auftrag:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")

    # Check if invoice exists - prevent editing if it does
    rechnung = db.query(Rechnung).filter(Rechnung.auftrag_id == auftrag_id).first()
    if rechnung:
        raise HTTPException(
            status_code=400,
            detail="Auftrag kann nicht bearbeitet werden, da bereits eine Rechnung erstellt wurde."
        )

    # Update auftrag fields (status is not editable)
    auftrag.beschreibung = beschreibung
    auftrag.kunde_leistungsadresse = kunde_leistungsadresse
    auftrag.kunde_leistung_plz = kunde_leistung_plz
    auftrag.kunde_leistung_ort = kunde_leistung_ort

    if auftrag_start:
        try:
            auftrag.auftrag_start = datetime.datetime.strptime(auftrag_start, '%Y-%m-%d').date()
        except ValueError:
            pass  # Keep existing date if invalid format

    # Update arbeitskomponenten if provided
    if arbeitskomponenten:
        import json
        try:
            ak_data = json.loads(arbeitskomponenten)
            for ak_info in ak_data:
                ak_id = int(ak_info['id'])
                ak = db.query(ArbeitKomponente).filter(ArbeitKomponente.id == ak_id).first()
                if ak:
                    ak.arbeit = ak_info.get('arbeit')
                    ak.beschreibung = ak_info.get('beschreibung')

                    if ak_info.get('komponente_start'):
                        try:
                            ak.komponente_start = datetime.datetime.strptime(ak_info['komponente_start'], '%Y-%m-%d').date()
                        except ValueError:
                            pass

                    if ak_info.get('komponente_ende'):
                        try:
                            ak.komponente_ende = datetime.datetime.strptime(ak_info['komponente_ende'], '%Y-%m-%d').date()
                        except ValueError:
                            pass

                    ak.berechnungsbasis = ak_info.get('berechnungsbasis')

                    # Clear unused fields based on calculation basis
                    if ak.berechnungsbasis == 'stunden':
                        # Update Stunden fields
                        ak.anzahl_stunden = float(ak_info['anzahl_stunden']) if ak_info.get('anzahl_stunden') else None
                        ak.stundenlohn = float(ak_info['stundenlohn']) if ak_info.get('stundenlohn') else None
                        # Clear Quadratmeter fields
                        ak.anzahl_quadrat = None
                        ak.preis_pro_quadrat = None
                    elif ak.berechnungsbasis == 'quadratmeter':
                        # Update Quadratmeter fields
                        ak.anzahl_quadrat = float(ak_info['anzahl_quadrat']) if ak_info.get('anzahl_quadrat') else None
                        ak.preis_pro_quadrat = float(ak_info['preis_pro_quadrat']) if ak_info.get('preis_pro_quadrat') else None
                        # Clear Stunden fields
                        ak.anzahl_stunden = None
                        ak.stundenlohn = None
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Fehler bei Arbeitskomponenten: {str(e)}")

    # Update materialkomponenten if provided
    if materialkomponenten:
        import json
        try:
            mk_data = json.loads(materialkomponenten)
            for mk_info in mk_data:
                mk_id = int(mk_info['id'])
                mk = db.query(MaterialKomponente).filter(MaterialKomponente.id == mk_id).first()
                if mk:
                    mk.bezeichnung = mk_info.get('bezeichnung')
                    mk.berechnungseinheit = mk_info.get('berechnungseinheit')
                    mk.anzahl = float(mk_info['anzahl']) if mk_info.get('anzahl') else None
                    mk.preis_pro_einheit = float(mk_info['preis_pro_einheit']) if mk_info.get('preis_pro_einheit') else None
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Fehler bei Materialkomponenten: {str(e)}")

    db.commit()

    return {"success": True, "message": "Auftrag erfolgreich aktualisiert"}
