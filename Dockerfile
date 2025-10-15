FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV APP_MODE=api
ENV PORT=7860

CMD if [ "$APP_MODE" = "api" ]; then \
        uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT; \
    else \
        streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0; \
    fi
