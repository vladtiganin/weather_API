from pydantic import BaseModel
from datetime import datetime


class CityWeatherData(BaseModel):
    temp: float
    description: str
    units: str


class GetWeatherResponse(BaseModel):
    city: str
    timestamp: datetime
    data: CityWeatherData


class GetResponseHistory(BaseModel):
    items: list[CityWeatherData]
    page: int
    limit: int
    total: int

