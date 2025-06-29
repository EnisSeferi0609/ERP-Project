from sqlalchemy import create_engine, extract, func
from sqlalchemy.orm import sessionmaker
from datetime import date
from collections import defaultdict
from app.models.rechnung import Rechnung
from app.models.kunde import Kunde
from app.models.auftrag import Auftrag
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.unternehmensstatistik import Unternehmensstatistik, KategorieEnum
from database.db import Base
import os

# Datenbankverbindung
DATABASE_URL = "sqlite:///erp.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Hilfsfunktion: Check ob Eintrag bereits existiert
def existiert_bereits(monat, jahr, kategorie):
    return session.query(Unternehmensstatistik).filter(
        extract("month", Unternehmensstatistik.datum) == monat,
        extract("year", Unternehmensstatistik.datum) == jahr,
        Unternehmensstatistik.kategorie == kategorie
    ).first() is not None

# Ergebnisse sammeln
monatsdaten = defaultdict(lambda: defaultdict(float))

# Umsatz
umsatzdaten = session.query(
    extract("month", Rechnung.rechnungsdatum),
    extract("year", Rechnung.rechnungsdatum),
    func.sum(Rechnung.rechnungssumme_gesamt)
).group_by(extract("year", Rechnung.rechnungsdatum), extract("month", Rechnung.rechnungsdatum)).all()

for monat, jahr, summe in umsatzdaten:
    monatsdaten[(int(jahr), int(monat))][KategorieEnum.UMSATZ] = summe

# Lohnkosten, Materialkosten, Stunden
komponenten = session.query(ArbeitKomponente).all()
for k in komponenten:
    if k.komponente_start:
        monat = k.komponente_start.month
        jahr = k.komponente_start.year
        if k.anzahl_stunden and k.stundenlohn:
            monatsdaten[(jahr, monat)][KategorieEnum.LOHNKOSTEN] += k.anzahl_stunden * k.stundenlohn
            monatsdaten[(jahr, monat)][KategorieEnum.STUNDEN] += k.anzahl_stunden
        if k.anzahl_quadrat and k.preis_pro_quadrat:
            monatsdaten[(jahr, monat)][KategorieEnum.MATERIALKOSTEN] += k.anzahl_quadrat * k.preis_pro_quadrat

# Aufträge
auftraege = session.query(Auftrag).filter(Auftrag.auftrag_start.isnot(None)).all()
for a in auftraege:
    monat = a.auftrag_start.month
    jahr = a.auftrag_start.year
    monatsdaten[(jahr, monat)][KategorieEnum.AUFTRAEGE] += 1

# Kunden
kunden = session.query(Kunde).filter(Kunde.kunde_seit.isnot(None)).all()
for k in kunden:
    monat = k.kunde_seit.month
    jahr = k.kunde_seit.year
    monatsdaten[(jahr, monat)][KategorieEnum.KUNDENANFRAGEN] += 1
    monatsdaten[(jahr, monat)][KategorieEnum.NEUKUNDEN] += 1

# Ergebnisse speichern
for (jahr, monat), werte in monatsdaten.items():
    for kategorie, wert in werte.items():
        if not existiert_bereits(monat, jahr, kategorie):
            eintrag = Unternehmensstatistik(
                datum=date(jahr, monat, 1),
                kategorie=kategorie,
                wert=wert,
                einheit="€" if "KOSTEN" in kategorie.name or kategorie == KategorieEnum.UMSATZ else "Stück" if "AUFTRAEGE" in kategorie.name or "KUNDEN" in kategorie.name else "Stunden"
            )
            session.add(eintrag)

session.commit()
session.close()
print("✅ Monatliche Statistiken erfolgreich aktualisiert.")

