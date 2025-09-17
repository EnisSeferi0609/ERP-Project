"""Customer data models for private and business customers."""


from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.orm import relationship
from database.db import Base


class Kunde(Base):
    """Customer model for private and business customers.

    Supports both private customers (Privatkunden) and business customers (Gewerbekunden)
    with conditional fields based on customer type.
    """
    __tablename__ = "kunde"

    id = Column(Integer, primary_key=True)

    kundenart = Column(String)
    kunde_firmenname = Column(String)
    kunde_gesellschaftsform = Column(String)
    ansprechpartner_vorname = Column(String)
    ansprechpartner_nachname = Column(String)
    kunde_vorname = Column(String)
    kunde_nachname = Column(String)
    kunde_rechnungsadresse = Column(String)
    kunde_rechnung_plz = Column(String)
    kunde_rechnung_ort = Column(String)
    kunde_email = Column(String)
    kunde_telefon = Column(String)
    notizen = Column(Text)
    kunde_seit = Column(Date)

    rechnungen = relationship("Rechnung", back_populates="kunde")
    auftraege = relationship(
        "Auftrag",
        back_populates="kunde",
        cascade="all, delete-orphan"
    )
