from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from collections import defaultdict

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
    zahlungsart: str = Form(""),
    db: Session = Depends(get_db)
):
    buchung = EinnahmeAusgabe(
        datum=datum,
        betrag=betrag,
        typ=typ.lower(),
        kategorie_id=kategorie_id,
        beschreibung=beschreibung,
        zahlungsart=zahlungsart
    )
    db.add(buchung)
    db.commit()
    return RedirectResponse("/euer", status_code=303)


# Rechnung als bezahlt/unbezahlt markieren & Buchung erzeugen
@router.post("/rechnung/{rechnung_id}/status")
def rechnung_status_toggle(rechnung_id: int, db: Session = Depends(get_db)):
    rechnung = db.query(Rechnung).filter(Rechnung.id == rechnung_id).first()
    if not rechnung:
        return HTMLResponse("Nicht gefunden", status_code=404)

    rechnung.bezahlt = not rechnung.bezahlt
    db.commit()

    # Falls bezahlt, automatisch EÜR-Buchung erzeugen
    if rechnung.bezahlt:
        kategorie = db.query(EurKategorie).filter_by(
            name="Erlöse", typ="einnahme").first()
        if kategorie:
            buchung = EinnahmeAusgabe(
                datum=date.today(),
                betrag=rechnung.betrag,
                typ="einnahme",
                kategorie_id=kategorie.id,
                beschreibung=(
                    f"Rechnung {rechnung.id} – {rechnung.beschreibung or ''}"
                ),
                zahlungsart="Überweisung",
                rechnung_id=rechnung.id)
            db.add(buchung)
            db.commit()

    return RedirectResponse("/rechnungsliste", status_code=303)


@router.get("/euer", response_class=HTMLResponse)
def euer_uebersicht(request: Request, db: Session = Depends(get_db)):
    eintraege = db.query(EinnahmeAusgabe).all()

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
        "eintraege": eintraege,
        "einnahmen_summe": einnahmen_summe,
        "ausgaben_summe": ausgaben_summe,
        "saldo": saldo,
        "labels": labels,
        "daten_einnahmen": daten_einnahmen,
        "daten_ausgaben": daten_ausgaben
    })
