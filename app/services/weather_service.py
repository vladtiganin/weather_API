from httpx import AsyncClient, HTTPStatusError, RequestError
from datetime import date
from time import perf_counter

from app.schemas.weather_schemas import *
from app.config import settings
from app.core.exception.exception import (
    CityNotFoundError,
    InvalidHistoryRangeError,
    WeatherProviderAuthError,
    WeatherProviderError,
    WeatherResponseFormatError,
)
from app.core.logging import get_logger
from app.repositories.weather_repo import WeatherRepository
from app.models.request_model import RequestORM


logger = get_logger(__name__)


class WeatherService():
    def __init__(self, weather_repo: WeatherRepository):
        self.weather_repo = weather_repo


    async def get_weather(self, city: str, unit: str) -> GetWeatherResponse:
        city = city.capitalize()
        logger.info(
            "Weather request started",
            extra={
                "event": "weather_request_started",
                "city_name": city,
                "unit": unit,
            },
        )

        openweather_unit = {
            "celsius": "metric",
            "fahrenheit": "imperial",
        }[unit]

        last_query = await self.weather_repo.get_cached_record(city, unit)
        if last_query is not None:
            logger.info(
                "Weather cache hit",
                extra={
                    "event": "weather_cache_hit",
                    "city_name": city,
                    "unit": unit,
                    "cached_request_id": last_query.id,
                },
            )

            try:
                cached_data = last_query.data
                if not isinstance(cached_data, dict):
                    raise TypeError

                cached_data["description"]
                cached_data["temp"]
                cached_data["units"]
            except (KeyError, TypeError) as exc:
                logger.warning(
                    "Cached weather data has unexpected format",
                    exc_info=True,
                    extra={
                        "event": "weather_cached_response_format_failed",
                        "city_name": city,
                        "unit": unit,
                        "cached_request_id": last_query.id,
                    },
                )
                raise WeatherResponseFormatError() from exc

            orm = await self.weather_repo.add_weather_query(
                city=last_query.city_name,
                data=cached_data,
                served_from_cache=True
            )

            logger.info(
                "Weather response saved",
                extra={
                    "event": "weather_response_saved",
                    "request_id": orm.id,
                    "city_name": orm.city_name,
                    "served_from_cache": orm.served_from_cache,
                },
            )

            return {
                "city_name": orm.city_name,
                "timestamp": orm.timestamp,
                "served_from_cache": orm.served_from_cache,
                "data": orm.data,
            }

        logger.info(
            "Weather cache miss",
            extra={
                "event": "weather_cache_miss",
                "city_name": city,
                "unit": unit,
            },
        )

        try:
            logger.info(
                "Weather provider request started",
                extra={
                    "event": "weather_provider_request_started",
                    "city_name": city,
                    "unit": unit,
                },
            )

            provider_started_at = perf_counter()
            async with AsyncClient() as client:
                response = await client.get(
                    url="https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": city,
                        "units": openweather_unit,
                        "appid": settings.weather_api_key
                    }
                )
            provider_latency_ms = round((perf_counter() - provider_started_at) * 1000, 2)

            logger.info(
                "Weather provider request finished",
                extra={
                    "event": "weather_provider_request_finished",
                    "city_name": city,
                    "unit": unit,
                    "provider_status_code": response.status_code,
                    "latency_ms": provider_latency_ms,
                },
            )

            response.raise_for_status()
        except RequestError as exc:
            provider_latency_ms = round((perf_counter() - provider_started_at) * 1000, 2)
            logger.warning(
                "Weather provider request failed",
                exc_info=True,
                extra={
                    "event": "weather_provider_request_failed",
                    "city_name": city,
                    "unit": unit,
                    "latency_ms": provider_latency_ms,
                },
            )
            raise WeatherProviderError(city) from exc
        except HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning(
                "Weather provider returned error response",
                exc_info=True,
                extra={
                    "event": "weather_provider_request_failed",
                    "city_name": city,
                    "unit": unit,
                    "provider_status_code": status_code,
                },
            )

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
            logger.warning(
                "Weather provider response has unexpected format",
                exc_info=True,
                extra={
                    "event": "weather_provider_response_format_failed",
                    "city_name": city,
                    "unit": unit,
                },
            )
            raise WeatherResponseFormatError() from exc

        orm = await self.weather_repo.add_weather_query(city=city, data=res["data"])
        res.update({"timestamp": orm.timestamp})
        res.update({"served_from_cache": orm.served_from_cache})
        logger.info(
            "Weather response saved",
            extra={
                "event": "weather_response_saved",
                "request_id": orm.id,
                "city_name": orm.city_name,
                "served_from_cache": orm.served_from_cache,
            },
        )

        return res


    async def get_weather_history(self, city: str, page: int, limit: int, date_from: date | None = None, date_to: date | None = None) -> GetResponseHistory:
        logger.info(
            "Weather history requested",
            extra={
                "event": "history_requested",
                "city_name": city,
                "page": page,
                "limit": limit,
                "date_from": date_from,
                "date_to": date_to,
            },
        )

        if date_from and date_to and date_from > date_to:
            raise InvalidHistoryRangeError(date_from, date_to)

        history, total = await self.weather_repo.get_history(city, page, limit, date_from, date_to)

        res = {
            "items": history,
            "page": page,
            "limit": limit,
            "total": total
        }

        return res


    async def get_weather_history_export(self, city: str, date_from: date | None = None, date_to: date | None = None) -> list[RequestORM]:
        logger.info(
            "Weather history export requested",
            extra={
                "event": "history_export_requested",
                "city_name": city,
                "date_from": date_from,
                "date_to": date_to,
            },
        )

        if date_from and date_to and date_from > date_to:
            raise InvalidHistoryRangeError(date_from, date_to)

        return await self.weather_repo.get_weather_history_export(city, date_from, date_to)







