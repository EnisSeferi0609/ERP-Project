"""Invoice and billing management models."""

from sqlalchemy import Column, Integer, Date, Text, ForeignKey, Boolean, DECIMAL
from sqlalchemy.orm import relationship
from database.db import Base


class Rechnung(Base):
    """Invoice model for billing construction jobs.

    Links to customer, order, and company data. Supports payment tracking
    and EÜR (German tax) entries generation.
    """
    __tablename__ = "rechnung"

    id = Column(Integer, primary_key=True)

    kunde_id = Column(Integer, ForeignKey("kunde.id"), nullable=False)
    auftrag_id = Column(Integer, ForeignKey("auftrag.id"), nullable=False)
    unternehmensdaten_id = Column(
        Integer,
        ForeignKey("unternehmensdaten.id"),
        nullable=False)

    rechnungsdatum = Column(Date)
    faelligkeit = Column(Date)
    rechtlicher_hinweis = Column(Text)
    rechnungssumme_arbeit = Column(DECIMAL(12, 2))  # Higher precision for totals
    rechnungssumme_material = Column(DECIMAL(12, 2))  # Higher precision for totals
    rechnungssumme_gesamt = Column(DECIMAL(12, 2))  # Higher precision for totals
    bezahlt = Column(Boolean, default=False)
    payment_date = Column(Date, nullable=True)

    kunde = relationship("Kunde", back_populates="rechnungen")
    auftrag = relationship("Auftrag", back_populates="rechnungen")
    unternehmensdaten = relationship(
        "Unternehmensdaten",
        back_populates="rechnungen")
    einnahmen_ausgaben = relationship(
        "EinnahmeAusgabe",
        back_populates="rechnung",
        cascade="all, delete-orphan"
    )
