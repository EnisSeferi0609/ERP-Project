```python
#| ---
#| title: "DB Example"
#| author: "Enis Seferi"
#| format: pdf
#| jupyter: python3
#| ---
```


[markdown]

```python
# # Verbindung zur Datenbank
# 
# Dieses Skript initialisiert eine Verbindung zur SQLite-Datenbank
# und erstellt eine Session-Factory mithilfe von SQLAlchemy.
```





from sqlalchemy import create_engine

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./erp.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


def get_db():

    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```
---------------------------------------------------------------------------NameError
Traceback (most recent call last)Cell In[1], line 6
      2 from sqlalchemy.orm import sessionmaker, Session
      4 DATABASE_URL = "sqlite:///./erp.db"
----> 6 engine = create_engine(
      7     DATABASE_URL,
      8     connect_args={"check_same_thread": False}
      9 )
     12 SessionLocal = sessionmaker(
     13     autocommit=False,
     14     autoflush=False,
     15     bind=engine
     16 )
     19 Base = declarative_base()
NameError: name 'create_engine' is not defined
```

