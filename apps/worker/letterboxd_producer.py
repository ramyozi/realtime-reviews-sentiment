import asyncio
import datetime
import random
import re

import requests
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from apps.common.db import SessionLocal, Base, engine
from apps.common.models import Review
from langdetect import detect, DetectorFactory


DetectorFactory.seed = 0
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
    # On parcourt d'abord /reviews/popular/ puis /reviews/ en fallback
    for suffix in ["reviews/popular/", "reviews/"]:
        url = f"https://letterboxd.com/film/{slug}/{suffix}"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # ⚠️ On itère par review via l'article parent, car c’est là que sont author + url
        articles = soup.select("div.listitem article.production-viewing")
        if not articles:
            continue

        reviews_data = []

        for art in articles:
            # auteur (username) via l’avatar: <a class="avatar" href="/username/">
            author = None
            a_avatar = art.select_one("a.avatar[href^='/']")
            if a_avatar and a_avatar.get("href"):
                href = a_avatar["href"].strip("/")
                # href est typiquement "username"
                if href and "/" not in href:
                    author = href

            # URL exacte de la review via le lien de contexte:
            #     <a class="context" href="/username/film/<slug>[/<index>]/">
            review_url = None
            a_ctx = art.select_one(f"a.context[href*='/film/{slug}']")
            if a_ctx and a_ctx.get("href"):
                href = a_ctx["href"]
                review_url = "https://letterboxd.com" + href if href.startswith("/") else href

                # fallback pour author si pas trouvé: extraire depuis l’URL de contexte
                if not author:
                    # /<username>/film/<slug>/...
                    parts = href.split("/")
                    # ['', 'username', 'film', '<slug>', ...]
                    if len(parts) >= 3 and parts[1] and parts[2] == "film":
                        author = parts[1]

            # texte de la review (au sein de .js-review)
            # Certains cas ont un container spoiler puis un body texte, on prend le body-text le plus précis
            text_el = art.select_one("div.js-review div.body-text.-prose")
            if not text_el:
                # fallback léger: tout body-text dans .js-review
                text_el = art.select_one("div.js-review .body-text")

            if not text_el:
                continue  # pas de texte → skip

            # Texte + nettoyage minimal
            text = text_el.get_text(" ", strip=True)
            if not text or len(text) < 20:
                continue

            # langue depuis l’attribut 'lang' s’il est présent, sinon 'en' par défaut
            lang = text_el.get("lang") or "en"

            # Sécurité: on n’insère que si on a author + review_url (éviter l’URL générique /film/<slug>/reviews/)
            if not author or not review_url:
                continue

            # rating (0–10)
            rating = None
            rating_el = art.select_one("span.rating[class*='rated-']")
            if rating_el:
                m = re.search(r"rated-(\d+)",
                              rating_el.get("class", [None])[0] if isinstance(rating_el.get("class"), list) else
                              rating_el["class"])
                if m:
                    rating = float(m.group(1))  # note sur 10

            # timestamp de la review
            ts_review = None
            t_tag = art.select_one("time.timestamp[datetime]")
            if t_tag and t_tag.get("datetime"):
                try:
                    ts_review = datetime.fromisoformat(t_tag["datetime"])
                except Exception:
                    ts_review = None

            if not author or not review_url:
                continue

            reviews_data.append(
                {
                    "text": text,
                    "review_url": review_url,
                    "author": author,
                    "item_id": slug,
                    "lang": lang,
                    "review_rating": rating,
                    "ts_review": ts_review,
                }
            )

            # On arrête quand on a atteint la limite demandée
            if len(reviews_data) >= limit:
                break

        if reviews_data:
            return reviews_data

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
                text = rev["text"]
                score = analyzer.polarity_scores(text)["compound"]

                # ajuster légèrement le label pour éviter 0.0 systématique
                if score >= 0.1:
                    label = "pos"
                elif score <= -0.1:
                    label = "neg"
                else:
                    label = "neu"

                r = Review(
                    source="letterboxd",
                    item_id=rev["item_id"],
                    text=text,
                    review_url=rev["review_url"],
                    author=rev["author"],
                    lang=detect(text),
                    review_rating=rev.get("review_rating"),
                    ts_review=rev.get("ts_review"),
                    sentiment_score=score,
                    sentiment_label=label,
                )
                try:
                    db.add(r)
                    db.commit()
                    inserted += 1
                except IntegrityError:
                    db.rollback()
            print(f"✅ {inserted} nouvelles reviews ajoutées pour {slug}")
            await asyncio.sleep(30)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())