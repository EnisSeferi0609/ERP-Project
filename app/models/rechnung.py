from sqlalchemy import Column, Integer, Float, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base

class Rechnung(Base):
    __tablename__ = "rechnung"
    
    id = Column(Integer, primary_key=True)
    
    kunde_id = Column(Integer, ForeignKey("kunde.id"), nullable=False)
    auftrag_id = Column(Integer, ForeignKey("auftrag.id"), nullable=False)
    unternehmensdaten_id = Column(Integer, ForeignKey("unternehmensdaten.id"), nullable=False)
    
    rechnungsdatum = Column(Date)
    faelligkeit = Column(String)
    rechtlicher_hinweis = Column(Text)
    rechnungssumme_arbeit = Column(Float)
    rechnungssumme_material = Column(Float)
    rechnungssumme_gesamt = Column(Float)
    
    # Beziehungen
    kunde = relationship("Kunde", back_populates="rechnungen")
    auftrag = relationship("Auftrag", back_populates="rechnungen")
    unternehmensdaten = relationship("Unternehmensdaten", back_populates="rechnungen")

    
