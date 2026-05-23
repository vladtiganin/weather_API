from fastapi import FastAPI

from app.api.weather_api import router as weather_api_router
from app.core.exception.exception_handler import app_exception_handler
from app.core.exception.exception import AppException

app = FastAPI(
    title="Weather API",
    version="1.0.0"
)

app.include_router(weather_api_router)

app.add_exception_handler(AppException, app_exception_handler)

@app.get("/")
def root():
    return {"status": "ok"}

