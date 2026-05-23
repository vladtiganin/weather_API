from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from datetime import date

from app.core.exception.exception import WeatherStorageError
from app.models.request_model import RequestORM


class WeatherRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_weather_query(self, city: str, data: dict) -> RequestORM:
        req = RequestORM(
            city_name=city,
            data=data
        )

        try:
            self.session.add(req)
            await self.session.commit()
            await self.session.refresh(req)
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise WeatherStorageError() from exc

        return req


    async def get_history(self, city: str, date_from: date, date_to: date, page: int, limit: int) -> tuple[list[RequestORM], int]:
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
            raise WeatherStorageError() from exc

        return res, total
