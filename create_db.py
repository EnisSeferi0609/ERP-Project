# create_db.py

from database.db import Base, engine

from app.models.kunde import Kunde
from app.models.rechnung import Rechnung
from app.models.auftrag import Auftrag
from app.models.material_komponente import MaterialKomponente
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.unternehmensdaten import Unternehmensdaten

# Tabellen in der Datenbank anlegen
print("Erstelle Tabellen in der Datenbank...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Die Datenbank wurde erstellt.")
