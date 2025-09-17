"""Work components and labor tracking for construction orders."""

from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from database.db import Base


class ArbeitKomponente(Base):
    __tablename__ = "arbeit_komponente"

    id = Column(Integer, primary_key=True)
    auftrag_id = Column(Integer, ForeignKey("auftrag.id"), nullable=False)

    arbeit = Column(String)
    beschreibung = Column(Text)
    komponente_start = Column(Date)
    komponente_ende = Column(Date)
    berechnungsbasis = Column(String)
    anzahl_stunden = Column(Integer)
    anzahl_quadrat = Column(Integer)
    stundenlohn = Column(DECIMAL(10, 2))  # Precision: 10 digits, 2 decimal places
    preis_pro_quadrat = Column(DECIMAL(10, 2))  # Precision: 10 digits, 2 decimal places
    kategorie_id = Column(Integer, ForeignKey("eur_kategorie.id"))

    kategorie = relationship("EurKategorie", back_populates="arbeit_komponenten")

    # Beziehung zurück zum Auftrag
    auftrag = relationship("Auftrag", back_populates="arbeit_komponenten")
