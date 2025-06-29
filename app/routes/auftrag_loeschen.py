from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database.db import SessionLocal
from app.models.auftrag import Auftrag
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.material_komponente import MaterialKomponente
from app.models.rechnung import Rechnung


router = APIRouter()

# DB-Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Route zum Löschen eines Auftrags + Komponenten
@router.post("/auftrag/loeschen/{auftrag_id}")
def auftrag_loeschen(auftrag_id: int, db: Session = Depends(get_db)):
    auftrag = db.query(Auftrag).filter(Auftrag.id == auftrag_id).first()

    if not auftrag:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")

    # Arbeits- und Materialkomponenten löschen
    db.query(ArbeitKomponente).filter(ArbeitKomponente.auftrag_id == auftrag_id).delete()
    db.query(MaterialKomponente).filter(MaterialKomponente.auftrag_id == auftrag_id).delete()

    db.query(Rechnung).filter(Rechnung.auftrag_id == auftrag_id).delete()

    # Auftrag löschen
    db.delete(auftrag)
    db.commit()

    return RedirectResponse(url="/kundenliste", status_code=303)
