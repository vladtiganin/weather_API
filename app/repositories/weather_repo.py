from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.models.request_model import RequestORM


class WeatherRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_weather_query(self, city: str, data: dict) -> RequestORM:
        req = RequestORM(
            city_name=city,
            data=data
        )

        self.session.add(req)
        await self.session.commit()
        await self.session.refresh(req)
        return req


    async def get_history(self, city: str, date_from: date, date_to: date, page: int, limit: int) -> list[RequestORM]:
        statement = select(RequestORM)

        if city:
            statement = statement.where(RequestORM.city_name.ilike(f"%{city}%"))

        if date_from:
            statement = statement.where(RequestORM.query_timestamp >= date_from)

        if date_to:
            statement = statement.where(RequestORM.query_timestamp <= date_to)

        statement = (
            statement
            .order_by(RequestORM.query_timestamp.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        res = await self.session.execute(statement)
        return res.scalars.all()
