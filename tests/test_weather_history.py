from datetime import date

import pytest
from sqlalchemy.dialects import postgresql

from app.repositories.weather_repo import WeatherRepository


class FakeCountResult:
    def scalar_one(self):
        return 42


class FakeRowsResult:
    def scalars(self):
        return self

    def all(self):
        return ["row-1", "row-2"]


class FakeAsyncSession:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)

        if len(self.statements) == 1:
            return FakeCountResult()

        return FakeRowsResult()


@pytest.mark.asyncio
async def test_get_history_applies_city_date_filters_and_pagination():
    session = FakeAsyncSession()
    repo = WeatherRepository(session=session)

    rows, total = await repo.get_history(
        city="London",
        page=2,
        limit=10,
        date_from=date(2026, 5, 1),
        date_to=date(2026, 5, 24),
    )

    data_query = session.statements[1]
    compiled = data_query.compile(dialect=postgresql.dialect())
    sql = str(compiled)
    params = compiled.params

    assert rows == ["row-1", "row-2"]
    assert total == 42
    assert len(session.statements) == 2
    assert "city_name" in sql
    assert "timestamp" in sql
    assert "LIMIT" in sql
    assert "OFFSET" in sql
    assert "%London%" in params.values()
    assert date(2026, 5, 1) in params.values()
    assert date(2026, 5, 24) in params.values()
    assert 10 in params.values()
