from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CityWeatherData(BaseModel):
    temp: float
    description: str
    units: str


class GetWeatherResponse(BaseModel):
    city_name: str
    timestamp: datetime
    served_from_cache: bool 
    data: CityWeatherData


class WeatherHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    city_name: str
    timestamp: datetime
    data: CityWeatherData


class GetResponseHistory(BaseModel):
    items: list[WeatherHistoryItem]
    page: int
    limit: int
    total: int


