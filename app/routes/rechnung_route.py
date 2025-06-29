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


import pdfkit
import datetime
import os
from pathlib import Path
import base64


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

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
    unternehmensdaten = db.query(Unternehmensdaten).first()  # ⬅️ hier neu
    return templates.TemplateResponse("formular_rechnung.html", {
        "request": request,
        "kunden": kunden,
        "auftraege": auftraege,
        "unternehmensdaten": unternehmensdaten  # ⬅️ hier neu
    })


@router.post("/rechnungen")
def rechnung_erstellen(
    request: Request,
    kunde_id: int = Form(...),
    auftrag_id: int = Form(...),
    db: Session = Depends(get_db)
):
    kunde = db.query(Kunde).filter(Kunde.id == kunde_id).first()
    auftrag = db.query(Auftrag).filter(Auftrag.id == auftrag_id).first()
    komponenten = db.query(ArbeitKomponente).filter(ArbeitKomponente.auftrag_id == auftrag_id).all()

    if not auftrag or not kunde or not komponenten:
        return HTMLResponse(content="Auftrag oder Kunde oder Arbeitskomponenten nicht gefunden.", status_code=404)

    gesamtsumme = sum((k.anzahl_stunden or 0) * (k.stundenlohn or 0) for k in komponenten)

    neue_rechnung = Rechnung(
    kunde_id=kunde.id,
    auftrag_id=auftrag.id,
    unternehmensdaten_id=1,  # Falls du nur ein Unternehmen hast, sonst dynamisch auswählen
    rechnungsdatum=datetime.date.today(),
    faelligkeit="14 Tage",
    rechtlicher_hinweis="Zahlbar ohne Abzug innerhalb von 14 Tagen.",
    rechnungssumme_arbeit=gesamtsumme,
    rechnungssumme_material=0.0,  # oder später berechnen
    rechnungssumme_gesamt=gesamtsumme  # oder + material wenn du es trennst
)

    db.add(neue_rechnung)
    db.commit()

    unternehmensdaten = db.query(Unternehmensdaten).first()  # ⬅️ hier ergänzt

    
    # Logo laden und in Base64 umwandeln
    with open("app/static/logo.png", "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')
    
    rendered_html = templates.get_template("rechnung_template.html").render({
        "kunde": kunde,
        "auftrag": auftrag,
        "komponenten": komponenten,
        "rechnung": neue_rechnung,
        "unternehmensdaten": unternehmensdaten,
        "logo_base64": logo_base64  # ⬅️ Übergabe an Template
    })


    # PDF-Export
    pdf_path = os.path.join(BASE_DIR, "rechnungen", f"Rechnung_{auftrag.id}.pdf")
    config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")
    pdfkit.from_string(rendered_html, pdf_path, configuration=config)

    return FileResponse(path=pdf_path, filename=f"Rechnung_{auftrag.id}.pdf", media_type="application/pdf")
