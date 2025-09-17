"""Company data management routes for business information and settings."""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database.db import get_db
from app.models.unternehmensdaten import Unternehmensdaten
from app.utils.template_utils import create_templates
import os
from pathlib import Path

router = APIRouter()

templates = create_templates()




@router.get("/unternehmensdaten", response_class=HTMLResponse)
def unternehmensdaten_formular(
        request: Request,
        db: Session = Depends(get_db)):
    daten = db.query(Unternehmensdaten).first()
    return templates.TemplateResponse("unternehmensdaten.html", {
        "request": request,
        "daten": daten
    })


@router.post("/unternehmensdaten/speichern")
def unternehmensdaten_speichern(
    request: Request,
    unternehmen_name: str = Form(...),
    unternehmen_adresse: str = Form(...),
    unternehmen_plz: str = Form(...),
    unternehmen_ort: str = Form(...),
    unternehmen_steuernummer: str = Form(...),
    unternehmen_telefon: str = Form(...),
    zahlungsinfo_name: str = Form(...),
    zahlungsinfo_bank_name: str = Form(...),
    zahlungsinfo_iban: str = Form(...),
    zahlungsinfo_paypal: str = Form(...),
    rechtliche_informationen: str = Form(""),
    db: Session = Depends(get_db)
):
    daten = db.query(Unternehmensdaten).first()
    if daten:
        daten.unternehmen_name = unternehmen_name
        daten.unternehmen_adresse = unternehmen_adresse
        daten.unternehmen_plz = unternehmen_plz
        daten.unternehmen_ort = unternehmen_ort
        daten.unternehmen_steuernummer = unternehmen_steuernummer
        daten.unternehmen_telefon = unternehmen_telefon
        daten.zahlungsinfo_name = zahlungsinfo_name
        daten.zahlungsinfo_bank_name = zahlungsinfo_bank_name
        daten.zahlungsinfo_iban = zahlungsinfo_iban
        daten.zahlungsinfo_paypal = zahlungsinfo_paypal
        daten.rechtliche_informationen = rechtliche_informationen
    else:
        daten = Unternehmensdaten(
            unternehmen_name=unternehmen_name,
            unternehmen_adresse=unternehmen_adresse,
            unternehmen_plz=unternehmen_plz,
            unternehmen_ort=unternehmen_ort,
            unternehmen_steuernummer=unternehmen_steuernummer,
            unternehmen_telefon=unternehmen_telefon,
            zahlungsinfo_name=zahlungsinfo_name,
            zahlungsinfo_bank_name=zahlungsinfo_bank_name,
            zahlungsinfo_iban=zahlungsinfo_iban,
            zahlungsinfo_paypal=zahlungsinfo_paypal,
            rechtliche_informationen=rechtliche_informationen
        )
        db.add(daten)

    db.commit()
    return RedirectResponse(url="/unternehmensdaten", status_code=303)
