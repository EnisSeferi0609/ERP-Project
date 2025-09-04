from collections import defaultdict
from datetime import date

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.rechnung import Rechnung
from app.models.kunde import Kunde
from app.models.auftrag import Auftrag
from app.models.arbeit_komponente import ArbeitKomponente
from app.models.unternehmensstatistik import (
    Unternehmensstatistik, KategorieEnum
)

from database.db import SessionLocal


def update_statistiken() -> None:
    """Aggregiert Monatsstatistiken und speichert fehlende
    Einträge in Unternehmensstatistik."""
    session: Session = SessionLocal()
    try:
        # Hilfsfunktion: Prüfen, ob Eintrag bereits existiert
        def existiert_bereits(
                monat: int,
                jahr: int,
                kategorie: KategorieEnum) -> bool:
            return session.query(Unternehmensstatistik).filter(
                extract("month", Unternehmensstatistik.datum) == monat,
                extract("year", Unternehmensstatistik.datum) == jahr,
                Unternehmensstatistik.kategorie == kategorie
            ).first() is not None

        # Ergebnisse sammeln
        monatsdaten: dict[tuple[int, int], dict[KategorieEnum, float]] = \
            defaultdict(lambda: defaultdict(float))

        # Umsatz (Summe je Monat/Jahr)
        umsatzdaten = session.query(
            extract("month", Rechnung.rechnungsdatum),
            extract("year", Rechnung.rechnungsdatum),
            func.sum(Rechnung.rechnungssumme_gesamt)
        ).group_by(
            extract("year", Rechnung.rechnungsdatum),
            extract("month", Rechnung.rechnungsdatum)
        ).all()

        for monat, jahr, summe in umsatzdaten:
            if summe is not None:
                monatsdaten[(int(jahr), int(monat))
                            ][KategorieEnum.UMSATZ] = float(summe)

        # Lohnkosten, Materialkosten, Stunden
        for k in session.query(ArbeitKomponente).all():
            if k.komponente_start:
                monat = k.komponente_start.month
                jahr = k.komponente_start.year
                if k.anzahl_stunden and k.stundenlohn:
                    lohnkosten = float(k.anzahl_stunden) * float(k.stundenlohn)
                    monatsdaten[(jahr, monat)][
                        KategorieEnum.LOHNKOSTEN] += lohnkosten
                    monatsdaten[(jahr, monat)][
                        KategorieEnum.STUNDEN] += float(k.anzahl_stunden)
                if k.anzahl_quadrat and k.preis_pro_quadrat:
                    materialkosten = (float(k.anzahl_quadrat) *
                                      float(k.preis_pro_quadrat))
                    monatsdaten[(jahr, monat)][
                        KategorieEnum.MATERIALKOSTEN] += materialkosten

        # Aufträge (Zählung)
        for a in session.query(Auftrag).filter(
                Auftrag.auftrag_start.isnot(None)).all():
            monatsdaten[(a.auftrag_start.year, a.auftrag_start.month)
                        ][KategorieEnum.AUFTRAEGE] += 1.0

        # Kunden (Zählung)
        for k in session.query(Kunde).filter(
                Kunde.kunde_seit.isnot(None)).all():
            key = (k.kunde_seit.year, k.kunde_seit.month)
            monatsdaten[key][KategorieEnum.KUNDENANFRAGEN] += 1.0
            monatsdaten[key][KategorieEnum.NEUKUNDEN] += 1.0

        # Ergebnisse speichern (nur fehlende)
        for (jahr, monat), werte in monatsdaten.items():
            for kategorie, wert in werte.items():
                if not existiert_bereits(monat, jahr, kategorie):
                    einheit = (
                        "€" if (
                            kategorie in {
                                KategorieEnum.LOHNKOSTEN,
                                KategorieEnum.MATERIALKOSTEN,
                                KategorieEnum.UMSATZ}) else "Stück" if (
                            kategorie in {
                                KategorieEnum.AUFTRAEGE,
                                KategorieEnum.KUNDENANFRAGEN,
                                KategorieEnum.NEUKUNDEN}) else "Stunden" if (
                            kategorie == KategorieEnum.STUNDEN) else "")
                    session.add(Unternehmensstatistik(
                        datum=date(jahr, monat, 1),
                        kategorie=kategorie,
                        wert=float(wert),
                        einheit=einheit
                    ))

        session.commit()
        print("✅ Monatliche Statistiken erfolgreich aktualisiert.")
    finally:
        session.close()


if __name__ == "__main__":
    update_statistiken()
