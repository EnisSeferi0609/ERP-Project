from sqlalchemy import Column, Integer, String, Float, Date, Enum
from database.db import Base
import enum

class KategorieEnum(enum.Enum):
    UMSATZ = "Umsatz"
    KOSTEN = "Kosten"
    MATERIALKOSTEN = "Materialkosten"
    LOHNKOSTEN = "Lohnkosten"
    STUNDEN = "Arbeitsstunden"
    AUFTRAEGE = "Aufträge"
    KUNDENANFRAGEN = "Kundenanfragen"
    NEUKUNDEN = "Neukunden"

class Unternehmensstatistik(Base):
    __tablename__ = "unternehmensstatistik"

    id = Column(Integer, primary_key=True)
    datum = Column(Date, nullable=False)
    kategorie = Column(Enum(KategorieEnum), nullable=False)  # Enum statt String
    wert = Column(Float, nullable=False)
    einheit = Column(String)
