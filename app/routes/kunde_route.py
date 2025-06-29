print("✅ kunde_route.py wird geladen")
from fastapi import APIRouter, Request, Form, Depends, HTTPException

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database.db import SessionLocal
from app.models.kunde import Kunde
import datetime
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import joinedload 
from app.models.rechnung import Rechnung
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.material_komponente import MaterialKomponente


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/kunde", response_class=HTMLResponse)
def formular_anzeigen(request: Request, db: Session = Depends(get_db)):
    kunden = db.query(Kunde).all()
    return templates.TemplateResponse("formular_kunde.html", {
        "request": request,
        "kunden": kunden
    })


@router.get("/kundenliste", response_class=HTMLResponse)
def kunden_liste(request: Request, db: Session = Depends(get_db)):
    kunden = db.query(Kunde).options(joinedload(Kunde.auftraege)).all()
    return templates.TemplateResponse("kunden_liste.html", {"request": request, "kunden": kunden})



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
    db: Session = Depends(get_db)
):
    if bestehend == "ja":
        if not kunde_id:
            raise HTTPException(status_code=400, detail="Kein bestehender Kunde ausgewählt.")
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
        neuer_kunde = Kunde(
            kundenart=kundenart,
            kunde_firmenname=kunde_firmenname if kundenart == "Gewerbekunde" else None,
            kunde_gesellschaftsform=kunde_gesellschaftsform if kundenart == "Gewerbekunde" else None,
            ansprechpartner_vorname=ansprechpartner_vorname if kundenart == "Gewerbekunde" else None,
            ansprechpartner_nachname=ansprechpartner_nachname if kundenart == "Gewerbekunde" else None,
            kunde_vorname=kunde_vorname if kundenart == "Privatkunde" else None,
            kunde_nachname=kunde_nachname if kundenart == "Privatkunde" else None,
            kunde_rechnungsadresse=kunde_rechnungsadresse,
            kunde_rechnung_plz=kunde_rechnung_plz,
            kunde_rechnung_ort=kunde_rechnung_ort,
            kunde_email=kunde_email,
            kunde_telefon=kunde_telefon,
            notizen=notizen,
            kunde_seit=datetime.date.today()
        )
        db.add(neuer_kunde)
        db.commit()

    return RedirectResponse("/kundenliste", status_code=303)


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
        "notizen": kunde.notizen
    }


@router.post("/kunde/loeschen/{kunde_id}")
def kunde_loeschen(kunde_id: int, db: Session = Depends(get_db)):
    kunde = db.query(Kunde).filter(Kunde.id == kunde_id).first()
    if not kunde:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    # Alle Aufträge dieses Kunden abrufen
    for auftrag in kunde.auftraege:
        db.query(ArbeitKomponente).filter(ArbeitKomponente.auftrag_id == auftrag.id).delete()
        db.query(MaterialKomponente).filter(MaterialKomponente.auftrag_id == auftrag.id).delete()
        db.query(Rechnung).filter(Rechnung.auftrag_id == auftrag.id).delete()
        db.delete(auftrag)

    # Dann den Kunden löschen
    db.delete(kunde)
    db.commit()

    return RedirectResponse(url="/kundenliste", status_code=303)

