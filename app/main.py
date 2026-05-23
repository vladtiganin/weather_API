from fastapi import FastAPI

from app.api.weather_api import router as weather_api_router

app = FastAPI(
    title="Weather API",
    version="1.0.0"
)

app.include_router(weather_api_router)

@app.get("/")
def root():
    return {"status": "ok"}

