# Realtime Reviews Sentiment

MVP en petites étapes. Voir la section 'How to run' à chaque commit tagué.

```bash
  git clone https://github.com/<ton-user>/realtime-reviews-sentiment.git
  cd realtime-reviews-sentiment
```

```bash
  python -m venv .venv
  source .venv/bin/activate  
```

```bash
  pip install -r requirements.txt
```

### API
``` bash 
    uvicorn -m apps.api.main:app  --reload --port 8000
```

### Worker (collecte + analyse)
``` bash 
  python -m apps.worker.letterboxd_producer
```

### Dashboard
```bash 
  streamlit run apps/dashboard/app.py --server.port 8501
```

### Tests rapides :
http://localhost:8000/reviews

### ou via Swagger UI :
http://localhost:8000/docs