"""Construction order and project management models."""

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class Auftrag(Base):
    """Construction order/project model.

    Represents a construction job with work and material components,
    linked to a customer and can have invoices generated.
    """
    __tablename__ = "auftrag"

    id = Column(Integer, primary_key=True)

    kunde_id = Column(Integer, ForeignKey("kunde.id"), nullable=False, index=True)

    status = Column(String)
    auftrag_start = Column(Date)
    beschreibung = Column(String)
    kunde_leistungsadresse = Column(String)
    kunde_leistung_plz = Column(String)
    kunde_leistung_ort = Column(String)

    kunde = relationship("Kunde", back_populates="auftraege")
    materialien = relationship(
        "MaterialKomponente",
        back_populates="auftrag",
        cascade="all, delete-orphan"
    )

    arbeit_komponenten = relationship(
        "ArbeitKomponente",
        back_populates="auftrag",
        cascade="all, delete-orphan"
    )
    rechnungen = relationship(
        "Rechnung",
        back_populates="auftrag",
        cascade="all, delete-orphan"
    )
