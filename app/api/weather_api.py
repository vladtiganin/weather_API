from fastapi import APIRouter, Depends, Query
from typing import Literal
from datetime import date
from typing import Annotated

from app.schemas.weather_schemas import *
from app.services.weather_service import WeatherService
from app.core.dependencies import get_weather_service_instance

router = APIRouter(
    prefix="/weather",
    tags= ["weather"]
)


@router.get("/", response_model=GetWeatherResponse)
async def get_weather_endpoint(
    city: Annotated[str, Query(min_length=1, max_length=100)],
    unit: Annotated[str, Literal["celsius", "fahrenheit"]],
    weather_service: WeatherService = Depends(get_weather_service_instance)
    
):
    return await weather_service.get_weather(city, unit)


@router.get("/history", response_model=GetResponseHistory)
async def get_history(
    city: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=0, le=100)] = 10,
    weather_service: WeatherService = Depends(get_weather_service_instance)
):
    return await weather_service.get_weather_hostory(city, date_from, date_to, page, limit)