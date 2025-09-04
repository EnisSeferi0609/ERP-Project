from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from database.db import Base
from sqlalchemy.orm import relationship


class EinnahmeAusgabe(Base):
    __tablename__ = "einnahmen_ausgaben"

    id = Column(Integer, primary_key=True)
    datum = Column(Date, nullable=False)
    typ = Column(String, nullable=False)  # 'einnahme' oder 'ausgabe'
    betrag = Column(Float, nullable=False)
    beschreibung = Column(String)
    zahlungsart = Column(String)
    belegpfad = Column(String)

    kategorie_id = Column(
        Integer,
        ForeignKey("eur_kategorie.id"),
        nullable=False)
    kategorie = relationship("EurKategorie", back_populates="einnahmen_ausgaben")

    rechnung_id = Column(Integer, ForeignKey("rechnung.id"), nullable=True)

    rechnung = relationship("Rechnung", back_populates="einnahmen_ausgaben")
