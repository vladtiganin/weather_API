from httpx import AsyncClient
from datetime import date

from app.schemas.weather_schemas import *
from app.config import settings
from app.repositories.weather_repo import WeatherRepository


class WeatherService():
    def __init__(self, weather_repo: WeatherRepository):
        self.weather_repo = weather_repo


    async def get_weather(self, city: str, unit: str) -> GetWeatherResponse:
        city = city.capitalize()
        openweather_unit = {
            "celsius": "metric",
            "fahrenheit": "imperial",
        }[unit]


        async with AsyncClient() as client:
            response = await client.post(
                url="https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "units": openweather_unit,
                    "appid": settings.weather_api_key
                }
            )

        response.raise_for_status()
        data = response.json()
        res = {
            "city": city,
            "data": {
                "description": data["weather"][0]["description"],
                "temp": data["main"]["temp"],
                "units": unit
            }
        }

        req = await self.weather_repo.add_weather_query(city=city, data=res["data"])

        return res


    async def get_weather_hostory(self, city: str, date_from: date, date_to: date, page: int, limit: int) -> GetResponseHistory:
        history = await self.weather_repo.get_history(city, date_from, date_to, page, limit)

        res = {
            "items": history,
            "page": page,
            "limit": limit,
            "total": len(history)
        }

        return res


