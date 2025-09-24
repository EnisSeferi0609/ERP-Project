"""Material cost components for construction orders."""

from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from database.db import Base


class MaterialKomponente(Base):
    __tablename__ = "material_komponente"

    id = Column(Integer, primary_key=True)
    auftrag_id = Column(Integer, ForeignKey("auftrag.id"), nullable=False, index=True)

    bezeichnung = Column(String, nullable=False)
    berechnungseinheit = Column(String)
    anzahl = Column(DECIMAL(10, 3), default=1.0)  # Allow 3 decimal places for quantities
    preis_pro_einheit = Column(DECIMAL(10, 2))  # Selling price (what customer pays)
    actual_cost = Column(DECIMAL(10, 2), nullable=True)  # Actual cost (what you paid)
    receipt_path = Column(String, nullable=True)  # Path to uploaded receipt
    kategorie_id = Column(Integer, ForeignKey("eur_kategorie.id"), index=True)

    kategorie = relationship("EurKategorie", back_populates="material_komponenten")

    # Beziehung zurück zum Auftrag
    auftrag = relationship("Auftrag", back_populates="materialien")
