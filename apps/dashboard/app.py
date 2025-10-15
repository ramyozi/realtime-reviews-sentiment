import time
import altair as alt
import pandas as pd
import requests
import streamlit as st
from pathlib import Path
import base64

API_URL = "https://realtime-reviews-sentiment.onrender.com/reviews?limit=100"

st.set_page_config(page_title="🎬 Analyse des Sentiments Letterboxd en Temps Réel", layout="wide")

LOGO_PATH  = Path(__file__).parent / "images/logo.svg"
GITHUB_URL = "https://github.com/ramyozi/realtime-reviews-sentiment"

if LOGO_PATH.exists():
    with open(LOGO_PATH, "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode("utf-8")

    logo_html = f"""
    <div style='text-align:center; margin-top:-20px; margin-bottom:15px;'>
        <a href="{GITHUB_URL}" target="_blank" style="text-decoration:none;">
            <img src="data:image/svg+xml;base64,{logo_base64}" 
                 alt="Realtime Reviews Logo" 
                 width="140" 
                 style="display:block; margin:auto;">
        </a>
    </div>
    """
    st.markdown(logo_html, unsafe_allow_html=True)
else:
    st.warning(f"Logo not found at {LOGO_PATH}")

st.markdown(
    """
    <h1 style='text-align:center; font-size:2.5rem; margin-top:0;'>🎬 Tableau de Bord des Sentiments Letterboxd</h1>
    <p style='text-align:center; color:gray; font-size:1rem;'>
        Analyse des avis de films en temps réel, propulsée par <b>FastAPI</b>, <b>Streamlit</b> & <b>VADER</b>
    </p>
    """,
    unsafe_allow_html=True,
)

placeholder = st.empty()
REFRESH_INTERVAL = 15

while True:
    try:
        resp = requests.get(API_URL, timeout=10)
        data = resp.json()

        if not data:
            st.info("Aucune donnée pour le moment...")
            time.sleep(REFRESH_INTERVAL)
            continue

        df = pd.DataFrame(data)

        # Nettoyage rapide
        df["sentiment_label"] = df["sentiment_label"].fillna("neu")
        df["sentiment_score"] = df["sentiment_score"].fillna(0.0)
        df["lang"] = df["lang"].fillna("en")

        # --- Filtres ---
        st.sidebar.header("🔍 Filtres")
        film_list = sorted(df["item_id"].dropna().unique())
        film = st.sidebar.selectbox("🎥 Choisir un film", ["(Tous)"] + film_list)
        lang_list = sorted(df["lang"].dropna().unique())
        lang = st.sidebar.selectbox("🌍 Langue", ["(Toutes)"] + lang_list)

        if film != "(Tous)":
            df = df[df["item_id"] == film]
        if lang != "(Toutes)":
            df = df[df["lang"] == lang]

        st.sidebar.info(f"{len(df)} avis affichés")

        # --- KPIs ---
        total = len(df)
        pos = (df["sentiment_label"] == "pos").sum()
        neg = (df["sentiment_label"] == "neg").sum()
        neu = (df["sentiment_label"] == "neu").sum()
        avg_score = df["sentiment_score"].mean()

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Nombre total d'avis", total)
        col2.metric("Positifs", f"{pos/total*100:.0f} %")
        col3.metric("Négatifs", f"{neg/total*100:.0f} %")
        col4.metric("Neutres", f"{neu/total*100:.0f} %")
        col5.metric("Score moyen", f"{avg_score:.2f}")

        # --- Graph 1 : Répartition globale ---
        st.subheader("📊 Répartition des Sentiments (Tous les Avis)")
        chart_sent = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("sentiment_label", title="Sentiment"),
                y=alt.Y("count()", title="Nombre"),
                color=alt.Color("sentiment_label", legend=None,
                                scale=alt.Scale(domain=["pos", "neu", "neg"],
                                                range=["#2ecc71", "#95a5a6", "#e74c3c"])),
                tooltip=["sentiment_label", "count()"],
            )
            .properties(height=250)
        )
        st.altair_chart(chart_sent, use_container_width=True)

        # --- Graph 2 : Score moyen par film ---
        st.subheader("🎥 Score Moyen de Sentiment par Film")
        chart_movie = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("item_id", title="Film"),
                y=alt.Y("mean(sentiment_score)", title="Score Moyen du Sentiment"),
                color=alt.Color("item_id", legend=None),
                tooltip=["item_id", "mean(sentiment_score)"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_movie, use_container_width=True)

        # --- Graph 3 : Histogramme des notes ---
        if "review_rating" in df.columns and df["review_rating"].notnull().any():
            st.subheader("⭐ Distribution des Notes Utilisateurs (Letterboxd)")
            chart_rating = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("review_rating:Q", bin=alt.Bin(maxbins=10), title="Note Utilisateur (0–10)"),
                    y=alt.Y("count()", title="Nombre"),
                    color=alt.value("#3498db"),
                    tooltip=["count()", "review_rating"]
                )
                .properties(height=250)
            )
            st.altair_chart(chart_rating, use_container_width=True)

        # --- Graph 4 : Corrélation ---
        if "review_rating" in df.columns:
            st.subheader("💬 Corrélation entre la Note et le Sentiment")
            chart_corr = (
                alt.Chart(df)
                .mark_circle(size=60, opacity=0.7)
                .encode(
                    x=alt.X("review_rating", title="Note Utilisateur (Letterboxd)"),
                    y=alt.Y("sentiment_score", title="Score de Sentiment (VADER)"),
                    color=alt.Color("sentiment_label", legend=None,
                                    scale=alt.Scale(domain=["pos", "neu", "neg"],
                                                    range=["#2ecc71", "#95a5a6", "#e74c3c"])),
                    tooltip=["author", "review_rating", "sentiment_score", "item_id", "lang"]
                )
                .properties(height=300)
            )
            st.altair_chart(chart_corr, use_container_width=True)

        # --- Table ---
        st.subheader("🗒️ Derniers Avis")
        df_display = df[[
            "item_id","review_rating", "author", "lang", "sentiment_label", "sentiment_score", "text", "review_url"
        ]]
        df_display["color"] = df_display["sentiment_label"].map({
            "pos": "🟩 positif",
            "neg": "🟥 négatif",
            "neu": "⬜ neutre"
        })
        st.dataframe(
            df_display[["item_id", "review_rating", "author", "lang", "color", "sentiment_score", "text", "review_url"]],
            hide_index=True,
            use_container_width=True,
        )

        time.sleep(REFRESH_INTERVAL)
        st.rerun()

    except Exception as e:
        st.error(f"API error: {e}")
        time.sleep(REFRESH_INTERVAL)
