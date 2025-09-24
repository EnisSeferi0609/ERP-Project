"""Income and expense tracking for German EÜR tax compliance."""

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text, DECIMAL
from database.db import Base
from sqlalchemy.orm import relationship


class EinnahmeAusgabe(Base):
    __tablename__ = "einnahmen_ausgaben"

    id = Column(Integer, primary_key=True)
    datum = Column(Date, nullable=False, index=True)
    typ = Column(String, nullable=False)  # 'einnahme' oder 'ausgabe'
    betrag = Column(DECIMAL(12, 2), nullable=False)  # Precise currency amounts
    beschreibung = Column(String)
    receipt_files = Column(Text, nullable=True)  # JSON string of receipt file names

    kategorie_id = Column(
        Integer,
        ForeignKey("eur_kategorie.id"),
        nullable=False,
        index=True)
    kategorie = relationship("EurKategorie", back_populates="einnahmen_ausgaben")

    rechnung_id = Column(Integer, ForeignKey("rechnung.id"), nullable=True, index=True)

    rechnung = relationship("Rechnung", back_populates="einnahmen_ausgaben")
