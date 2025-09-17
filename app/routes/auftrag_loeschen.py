"""Order deletion routes with cascading cleanup of related data."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.db import get_db
from app.models.auftrag import Auftrag
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.material_komponente import MaterialKomponente
from app.models.rechnung import Rechnung
from app.models.einnahme_ausgabe import EinnahmeAusgabe


router = APIRouter()



@router.post("/auftrag/loeschen/{auftrag_id}")
def auftrag_loeschen(auftrag_id: int, db: Session = Depends(get_db)):
    auftrag = db.query(Auftrag).filter(Auftrag.id == auftrag_id).first()

    if not auftrag:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")

    # First, find all invoices for this auftrag to delete their EÜR entries
    rechnungen = db.query(Rechnung).filter(Rechnung.auftrag_id == auftrag_id).all()
    for rechnung in rechnungen:
        # Delete all EÜR entries for each invoice
        db.query(EinnahmeAusgabe).filter(EinnahmeAusgabe.rechnung_id == rechnung.id).delete()
    
    # Then delete invoices
    db.query(Rechnung).filter(Rechnung.auftrag_id == auftrag_id).delete()
    
    # Delete work and material components
    db.query(ArbeitKomponente).filter(
        ArbeitKomponente.auftrag_id == auftrag_id).delete()
    db.query(MaterialKomponente).filter(
        MaterialKomponente.auftrag_id == auftrag_id).delete()

    # Auftrag löschen
    db.delete(auftrag)
    db.commit()

    return RedirectResponse(url="/kundenliste", status_code=303)
