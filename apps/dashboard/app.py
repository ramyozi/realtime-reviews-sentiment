import time
import requests
import pandas as pd
import streamlit as st
import altair as alt

API_URL = "http://localhost:8000/reviews?limit=100"

st.set_page_config(page_title="🎬 Letterboxd Realtime Sentiment", layout="wide")
st.title("🎬 Realtime Letterboxd Sentiment Dashboard")

placeholder = st.empty()

REFRESH_INTERVAL = 15

while True:
    try:
        resp = requests.get(API_URL, timeout=10)
        data = resp.json()

        if not data:
            st.info("No data yet...")
            time.sleep(REFRESH_INTERVAL)
            continue

        df = pd.DataFrame(data)

        # Nettoyage rapide
        df["sentiment_label"] = df["sentiment_label"].fillna("neu")
        df["sentiment_score"] = df["sentiment_score"].fillna(0.0)
        df["lang"] = df["lang"].fillna("en")

        total = len(df)
        pos = (df["sentiment_label"] == "pos").sum()
        neg = (df["sentiment_label"] == "neg").sum()
        neu = (df["sentiment_label"] == "neu").sum()
        avg_score = df["sentiment_score"].mean()

        # KPIs
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total reviews", total)
        col2.metric("Positive", f"{pos/total*100:.0f} %")
        col3.metric("Negative", f"{neg/total*100:.0f} %")
        col4.metric("Neutral", f"{neu/total*100:.0f} %")
        col5.metric("Average score", f"{avg_score:.2f}")

        # Graph 1 : Répartition globale du sentiment
        st.subheader("📊 Sentiment Distribution (All Reviews)")
        chart_sent = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("sentiment_label", title="Sentiment"),
                y=alt.Y("count()", title="Count"),
                color=alt.Color("sentiment_label", legend=None,
                                scale=alt.Scale(domain=["pos", "neu", "neg"],
                                                range=["#2ecc71", "#95a5a6", "#e74c3c"])),
                tooltip=["sentiment_label", "count()"],
            )
            .properties(height=250)
        )
        st.altair_chart(chart_sent, use_container_width=True)

        # Graph 2 : Score moyen par film
        st.subheader("🎥 Average Sentiment Score per Movie")
        chart_movie = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("item_id", title="Movie"),
                y=alt.Y("mean(sentiment_score)", title="Average Sentiment Score"),
                color=alt.Color("item_id", legend=None),
                tooltip=["item_id", "mean(sentiment_score)"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_movie, use_container_width=True)

        # Table détaillée
        st.subheader("🗒️ Latest Reviews")
        df_display = df[[
            "item_id", "author", "lang", "sentiment_label", "sentiment_score", "text", "review_url"
        ]]
        df_display["color"] = df_display["sentiment_label"].map({
            "pos": "🟩 positive",
            "neg": "🟥 negative",
            "neu": "⬜ neutral"
        })
        st.dataframe(
            df_display[["item_id", "author", "lang", "color", "sentiment_score", "text", "review_url"]],
            hide_index=True,
            use_container_width=True,
        )

        # rafraîchissement automatique
        time.sleep(REFRESH_INTERVAL)
        st.rerun()

    except Exception as e:
        st.error(f"API error: {e}")
        time.sleep(REFRESH_INTERVAL)
