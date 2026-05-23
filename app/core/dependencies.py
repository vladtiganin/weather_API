from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.weather_repo import WeatherRepository
from app.services.weather_service import WeatherService


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_weather_service_instance(session: DbSession) -> WeatherService:
    weather_repo = WeatherRepository(session)
    return WeatherService(weather_repo)
