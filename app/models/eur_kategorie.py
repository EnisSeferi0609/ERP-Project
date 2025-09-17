"""EÜR (German tax) category definitions for income/expense classification."""

from sqlalchemy import Column, Integer, String, UniqueConstraint
from database.db import Base
from sqlalchemy.orm import relationship


class EurKategorie(Base):
    __tablename__ = "eur_kategorie"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    typ = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "name",
            "typ",
            name="uix_eurkat_name_typ"),
    )

    arbeit_komponenten = relationship(
        "ArbeitKomponente", back_populates="kategorie")
    material_komponenten = relationship(
        "MaterialKomponente", back_populates="kategorie")
    einnahmen_ausgaben = relationship(
        "EinnahmeAusgabe", back_populates="kategorie")

    def __repr__(self):
        return f"<EurKategorie {self.name} ({self.typ})>"
