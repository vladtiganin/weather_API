from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Literal
from datetime import date
from typing import Annotated
import csv
from io import StringIO

from app.schemas.weather_schemas import *
from app.services.weather_service import WeatherService
from app.core.dependencies import get_weather_service_instance
from app.core.exception.exception import WeatherResponseFormatError
from app.core.logging import get_logger
from app.core.rate_limiter import rate_limit_by_ip


logger = get_logger(__name__)

router = APIRouter(
    prefix="/weather",
    tags= ["weather"]
)


@router.get("", response_model=GetWeatherResponse, dependencies=[Depends(rate_limit_by_ip)])
async def get_weather_endpoint(
    city: Annotated[str, Query(min_length=1, max_length=100)],
    unit: Annotated[Literal["celsius", "fahrenheit"], Query()],
    weather_service: WeatherService = Depends(get_weather_service_instance)
    
):
    return await weather_service.get_weather(city, unit)


@router.get("/history", response_model=GetResponseHistory)
async def get_history(
    city: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    weather_service: WeatherService = Depends(get_weather_service_instance)
):
    return await weather_service.get_weather_history(city, page, limit, date_from, date_to)


@router.get("/history/export")
async def get_history_export_csv(
    city: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    weather_service: WeatherService = Depends(get_weather_service_instance)
):
    records = await weather_service.get_weather_history_export(city, date_from, date_to)

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "city_name",
        "temperature",
        "description",
        "unit",
        "served_from_cache",
        "timestamp",
    ])

    try:
        for record in records:
            writer.writerow([
                record.id,
                record.city_name,
                record.data["temp"],
                record.data["description"],
                record.data["units"],
                record.served_from_cache,
                record.timestamp.isoformat(),
            ])
    except (KeyError, TypeError) as exc:
        logger.warning(
            "Weather history export record has unexpected data format",
            exc_info=True,
            extra={
                "event": "history_export_record_format_failed",
                "city_name": city,
                "date_from": date_from,
                "date_to": date_to,
            },
        )
        raise WeatherResponseFormatError() from exc

    output.seek(0)
    logger.info(
        "Weather history CSV export created",
        extra={
            "event": "history_export_csv_created",
            "records_count": len(records),
            "city_name": city,
            "date_from": date_from,
            "date_to": date_to,
        },
    )

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=weather_history.csv"
        },
    )



