from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.db import Base

class Unternehmensdaten(Base):
    __tablename__ = "unternehmensdaten"

    id = Column(Integer, primary_key=True)

    unternehmen_name = Column(String)
    unternehmen_adresse = Column(String)
    unternehmen_plz = Column(String)
    unternehmen_ort = Column(String)
    unternehmen_steuernummer = Column(String)
    unternehmen_telefon = Column(String)

    zahlungsinfo_name = Column(String)
    zahlungsinfo_bank_name = Column(String)
    zahlungsinfo_iban = Column(String)
    zahlungsinfo_paypal = Column(String)

    # Beziehung zu Rechnungen (1:n)
    rechnungen = relationship("Rechnung", back_populates="unternehmensdaten")
