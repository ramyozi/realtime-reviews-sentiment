from sqlalchemy import Column, Integer, String, Float, DateTime, text, func, Text, UniqueConstraint
from .db import Base

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)  # ex: letterboxd
    item_id = Column(String, nullable=False)  # slug du film
    review_url = Column(String, nullable=True)  # lien vers la review (optionnel)
    author = Column(String, nullable=True)  # pseudo de l’auteur (si dispo)
    text = Column(Text, nullable=False)
    lang = Column(String, nullable=True, default="en")

    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String, nullable=True)

    ts_review = Column(DateTime, nullable=True)  # quand la review a été publiée
    ts_ingest = Column(DateTime, server_default=func.now())  # quand tu l’as enregistrée

    __table_args__ = (
        UniqueConstraint("source", "item_id", "text", name="uq_review_unique_text"),
    )