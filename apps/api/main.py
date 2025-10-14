from fastapi import FastAPI

app = FastAPI(title="Realtime Reviews API")

@app.get("/health")
def health():
    return {"status": "ok"}
