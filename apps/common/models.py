from sqlalchemy import Column, Integer, String, Float, DateTime, text, func
from .db import Base

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)
    item_id = Column(String, nullable=False)
    text = Column(String, nullable=False)
    lang = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String, nullable=True)
    ts_event = Column(DateTime, server_default=func.now())