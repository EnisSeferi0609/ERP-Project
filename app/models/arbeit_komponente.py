from sqlalchemy import Column, Integer, String, Text, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base
from app.models.eur_kategorie import EurKategorie

class ArbeitKomponente(Base):
    __tablename__ = "arbeit_komponente"

    id = Column(Integer, primary_key=True)
    auftrag_id = Column(Integer, ForeignKey("auftrag.id"), nullable=False)

    arbeit = Column(String)
    belegart = Column(String)
    flaeche_m2 = Column(Integer)
    bodenart = Column(String)
    beschreibung = Column(Text)
    komponente_start = Column(Date)
    komponente_ende = Column(Date)
    berechnungsbasis = Column(String)
    anzahl_stunden = Column(Integer)
    anzahl_quadrat = Column(Integer)
    stundenlohn = Column(Float)
    preis_pro_quadrat = Column(Float)
    kategorie_id = Column(Integer, ForeignKey("eur_kategorie.id"))
    
    kategorie = relationship("EurKategorie")

    # Beziehung zurück zum Auftrag
    auftrag = relationship("Auftrag", back_populates="arbeit_komponenten")

