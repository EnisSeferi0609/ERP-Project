from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class MaterialKomponente(Base):
    __tablename__ = "material_komponente"

    id = Column(Integer, primary_key=True)
    auftrag_id = Column(Integer, ForeignKey("auftrag.id"), nullable=False)

    bezeichnung = Column(String, nullable=False)
    berechnungseinheit = Column(String)
    anzahl = Column(Float, default=1.0)
    preis_pro_einheit = Column(Float)
    kategorie_id = Column(Integer, ForeignKey("eur_kategorie.id"))

    kategorie = relationship("EurKategorie", back_populates="material_komponenten")

    # Beziehung zurück zum Auftrag
    auftrag = relationship("Auftrag", back_populates="materialien")
