from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class MaterialKomponente(Base):
    __tablename__ = "material_komponente"

    id = Column(Integer, primary_key=True)

    auftrag_id = Column(Integer, ForeignKey("auftrag.id"), nullable=False)

    bezeichnung = Column(String, nullable=False)
    berechnungseinheit = Column(String)
    preis_pro_einheit = Column(Float)

    # Beziehung zurück zum Auftrag
    auftrag = relationship("Auftrag", back_populates="materialien")
