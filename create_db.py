from database.db import Base, engine, SessionLocal
from app.models.kunde import Kunde  # noqa: F401
from app.models.rechnung import Rechnung  # noqa: F401
from app.models.auftrag import Auftrag  # noqa: F401
from app.models.material_komponente import MaterialKomponente  # noqa: F401
from app.models.arbeit_komponente import ArbeitKomponente  # noqa: F401
from app.models.unternehmensdaten import Unternehmensdaten  # noqa: F401
from app.models.einnahme_ausgabe import EinnahmeAusgabe  # noqa: F401
from app.models.eur_kategorie import EurKategorie

from sqlalchemy.exc import IntegrityError


def create_schema():
    print("Erstelle Tabellen (falls nicht vorhanden)…")
    Base.metadata.create_all(bind=engine)
    print("Schema ok.")


def init_kategorien():
    kategorien = [
        ("Erlöse", "einnahme"),
        ("Gutschriften", "einnahme"),
        ("Materialerlöse", "einnahme"),
        ("Zinsen", "einnahme"),
        ("Materialkosten", "ausgabe"),
        ("Fahrtkosten", "ausgabe"),
        ("Miete", "ausgabe"),
        ("Versicherungen", "ausgabe"),
        ("Werbekosten", "ausgabe"),
        ("Telefon/Internet", "ausgabe"),
        ("Arbeitskleidung", "ausgabe"),
        ("Werkzeuge", "ausgabe"),
    ]
    with SessionLocal() as db:
        for name, typ in kategorien:
            exists = db.query(EurKategorie).filter_by(
                name=name, typ=typ).first()
            if not exists:
                db.add(EurKategorie(name=name, typ=typ))
        try:
            db.commit()
            print("Standardkategorien eingefügt/aktualisiert.")
        except IntegrityError:
            db.rollback()
            print("Hinweis: Unique-Constraint verletzt – "
                  "Kategorien existieren wohl schon.")


if __name__ == "__main__":
    create_schema()
    init_kategorien()
