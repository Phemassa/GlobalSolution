from fastapi import FastAPI

app = FastAPI(title="GS Climate API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "api"}


@app.get("/predict")
def predict_stub() -> dict:
    # Placeholder ate o modelo baseline ser conectado.
    return {"prediction": None, "message": "baseline pending"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
