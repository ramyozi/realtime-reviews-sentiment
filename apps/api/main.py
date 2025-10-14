from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from apps.common.db import Base, engine, SessionLocal
from apps.common.models import Review

# nouveau système lifespan qui remplace on_event qui est decripated
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ce bloc se lance au démarrage
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")
    yield
    # Ce bloc se lance à la fermeture (ici rien à faire pour le moment)

app = FastAPI(title="Realtime Reviews API", lifespan=lifespan)

# Dépendance pour obtenir une session SQLAlchemy
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint santé
@app.get("/health")
def health():
    return {"status": "ok"}

# Endpoint liste des reviews
@app.get("/reviews")
def list_reviews(limit: int = 20, db: Session = Depends(get_db)):
    """
    Retourne les reviews les plus récentes (limite par défaut = 20)
    """
    reviews = db.query(Review).order_by(Review.id.desc()).limit(limit).all()
    # Conversion manuelle car SQLAlchemy retourne des objets
    return [
        {
            "id": r.id,
            "source": r.source,
            "item_id": r.item_id,
            "text": r.text,
            "lang": r.lang,
            "sentiment_score": r.sentiment_score,
            "sentiment_label": r.sentiment_label,
            "author": r.author,
            "review_url": r.review_url,
            "ts_review": r.ts_review,
            "ts_ingest": r.ts_ingest,
        }
        for r in reviews
    ]
