import asyncio
import random
from bs4 import BeautifulSoup
import requests
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from apps.common.db import SessionLocal, Base, engine
from apps.common.models import Review

Base.metadata.create_all(bind=engine)

FILMS = [
    "hot-fuzz",
    "birdman-or-the-unexpected-virtue-of-ignorance",
    "nightcrawler",
    "the-batman"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (DataPortfolioProject/1.0)"
}

analyzer = SentimentIntensityAnalyzer()

def fetch_reviews(slug: str, limit: int = 5):
    """Scrappe les n premières reviews d’un film donné sur Letterboxd."""
    for suffix in ["reviews/popular/", "reviews/"]:
        url = f"https://letterboxd.com/film/{slug}/{suffix}"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            reviews_html = soup.select("div.body-text.-prose")
            if not reviews_html:
                continue

            reviews_data = []
            for r in reviews_html[:limit]:
                text = r.get_text(strip=True).replace("\n", " ")
                if len(text) < 40:
                    continue

                # parent peut être None → on protège
                parent = r.find_parent("li")
                review_url, author = None, None

                if parent:
                    url_tag = parent.select_one("a[href*='/review/']")
                    if url_tag and url_tag.get("href"):
                        review_url = "https://letterboxd.com" + url_tag["href"]

                    author_tag = parent.select_one("a.name")
                    if author_tag:
                        author = author_tag.get_text(strip=True)

                reviews_data.append(
                    {
                        "text": text,
                        "review_url": review_url,
                        "author": author,
                        "item_id": slug,
                    }
                )

            if reviews_data:
                return reviews_data
        else:
            continue
    print(f"⚠️ Aucune review trouvée pour {slug}")
    return []

async def main():
    print("🚀 Démarrage du producteur Letterboxd...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        while True:
            slug = random.choice(FILMS)
            reviews = fetch_reviews(slug)
            inserted = 0
            for rev in reviews:
                score = analyzer.polarity_scores(rev["text"])["compound"]
                if score > 0.2:
                    label = "pos"
                elif score < -0.2:
                    label = "neg"
                else:
                    label = "neu"

                r = Review(
                    source="letterboxd",
                    item_id=rev["item_id"],
                    text=rev["text"],
                    review_url=rev["review_url"],
                    author=rev["author"],
                    lang="en",
                    sentiment_score=score,
                    sentiment_label=label,
                )
                try:
                    db.add(r)
                    db.commit()
                    inserted += 1
                except IntegrityError:
                    db.rollback()  # doublon
            print(f"✅ {inserted} nouvelles reviews ajoutées pour {slug}")
            await asyncio.sleep(30)  # un intervalle plus doux pour Letterboxd
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())