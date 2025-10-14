from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Fichier SQLite local (dans ./data/app.db)
DATABASE_URL = "sqlite:///data/app.db"

# Création du moteur
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # requis pour SQLite + threads FastAPI
    future=True,
)

# Classe de base pour les modèles
class Base(DeclarativeBase):
    pass

# Session locale (pour injection FastAPI)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
