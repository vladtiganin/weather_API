from httpx import AsyncClient, HTTPStatusError, RequestError
from datetime import date

from app.schemas.weather_schemas import *
from app.config import settings
from app.core.exception.exception import (
    CityNotFoundError,
    InvalidHistoryRangeError,
    WeatherProviderAuthError,
    WeatherProviderError,
    WeatherResponseFormatError,
)
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


        try:
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
        except RequestError as exc:
            raise WeatherProviderError(city) from exc
        except HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 404:
                raise CityNotFoundError(city) from exc
            if status_code in (401, 403):
                raise WeatherProviderAuthError() from exc

            raise WeatherProviderError(city) from exc

        try:
            data = response.json()
            res = {
                "city_name": city,
                "data": {
                    "description": data["weather"][0]["description"],
                    "temp": data["main"]["temp"],
                    "units": unit
                },
                
            }
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise WeatherResponseFormatError() from exc

        orm = await self.weather_repo.add_weather_query(city=city, data=res["data"])
        res.update({"timestamp": orm.timestamp})

        return res


    async def get_weather_history(self, city: str, date_from: date, date_to: date, page: int, limit: int) -> GetResponseHistory:
        if date_from and date_to and date_from > date_to:
            raise InvalidHistoryRangeError(date_from, date_to)

        history, total = await self.weather_repo.get_history(city, date_from, date_to, page, limit)

        res = {
            "items": history,
            "page": page,
            "limit": limit,
            "total": total
        }

        return res


