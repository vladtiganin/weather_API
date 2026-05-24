from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, datetime, timezone, timedelta
from datetime import time

from app.core.exception.exception import WeatherStorageError
from app.core.logging import get_logger
from app.models.request_model import RequestORM


logger = get_logger(__name__)


class WeatherRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_weather_query(
        self,
        city: str,
        data: dict,
        served_from_cache: bool = False
    ) -> RequestORM:
        req = RequestORM(
            city_name=city,
            data=data,
            served_from_cache=served_from_cache
        )

        try:
            self.session.add(req)
            await self.session.commit()
            await self.session.refresh(req)
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.exception(
                "Failed to insert weather record",
                extra={
                    "event": "weather_record_insert_failed",
                    "city_name": city,
                    "served_from_cache": served_from_cache,
                },
            )
            raise WeatherStorageError() from exc

        logger.info(
            "Weather record inserted",
            extra={
                "event": "weather_record_inserted",
                "request_id": req.id,
                "city_name": req.city_name,
                "served_from_cache": req.served_from_cache,
            },
        )

        return req


    async def get_history(self, city: str, page: int, limit: int, date_from: date | None = None, date_to: date | None = None) -> tuple[list[RequestORM], int]:
        statement = select(RequestORM)

        if city:
            statement = statement.where(RequestORM.city_name.ilike(f"%{city}%"))

        if date_from:
            statement = statement.where(RequestORM.timestamp >= date_from)

        if date_to:
            statement = statement.where(RequestORM.timestamp <= date_to)

        try:
            count_statement = select(func.count()).select_from(statement.subquery())
            total = (await self.session.execute(count_statement)).scalar_one()


            statement = (
                statement
                .order_by(RequestORM.timestamp.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )

            res = (await self.session.execute(statement)).scalars().all()
        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to query weather history",
                extra={
                    "event": "history_query_failed",
                    "city_name": city,
                    "page": page,
                    "limit": limit,
                    "date_from": date_from,
                    "date_to": date_to,
                },
            )
            raise WeatherStorageError() from exc

        logger.info(
            "Weather history query completed",
            extra={
                "event": "history_query_completed",
                "city_name": city,
                "page": page,
                "limit": limit,
                "date_from": date_from,
                "date_to": date_to,
                "total": total,
            },
        )

        return res, total


    async def get_cached_record(self, city: str, unit: str) -> RequestORM | None :
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

        statement = (
            select(RequestORM)
            .where(RequestORM.city_name == city)
            .where(RequestORM.data["units"].as_string() == unit)
            .where(RequestORM.served_from_cache.is_(False))
            .where(RequestORM.timestamp >= five_minutes_ago)
            .order_by(RequestORM.timestamp.desc())
            .limit(1)
        )

        try:
            result = await self.session.execute(statement)
        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to query cached weather record",
                extra={
                    "event": "weather_cache_lookup_failed",
                    "city_name": city,
                    "unit": unit,
                },
            )
            raise WeatherStorageError() from exc

        return result.scalar_one_or_none()


    async def get_weather_history_export(self, city: str, date_from: date | None = None, date_to: date | None = None) -> list[RequestORM]:
        statement = select(RequestORM)

        if city:
            statement = statement.where(RequestORM.city_name.ilike(f"%{city}%"))

        if date_from:
            date_from_dt = datetime.combine(date_from, time.min)
            statement = statement.where(RequestORM.timestamp >= date_from_dt)

        if date_to:
            date_to_dt = datetime.combine(date_to, time.max)
            statement = statement.where(RequestORM.timestamp <= date_to_dt)

        try:
            statement = statement.order_by(RequestORM.timestamp.desc())
            result = await self.session.execute(statement)
        except SQLAlchemyError as exc:
            logger.exception(
                "Failed to export weather history",
                extra={
                    "event": "history_export_query_failed",
                    "city_name": city,
                    "date_from": date_from,
                    "date_to": date_to,
                },
            )
            raise WeatherStorageError() from exc

        records = list(result.scalars().all())
        logger.info(
            "Weather history export query completed",
            extra={
                "event": "history_export_query_completed",
                "city_name": city,
                "date_from": date_from,
                "date_to": date_to,
                "records_count": len(records),
            },
        )

        return records






