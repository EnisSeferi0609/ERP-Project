from app.models.eur_kategorie import EurKategorie
from database.db import SessionLocal

def init_kategorien():
    db = SessionLocal()

    kategorien = [
        ("Erlöse", "einnahme"),
        ("Gutschriften", "einnahme"),
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

    for name, typ in kategorien:
        if not db.query(EurKategorie).filter_by(name=name, typ=typ).first():
            db.add(EurKategorie(name=name, typ=typ))

    db.commit()
    db.close()
    print("Standardkategorien wurden eingefügt.")

if __name__ == "__main__":
    init_kategorien()

