from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.weather_service import WeatherService


@pytest.mark.asyncio
async def test_get_weather_reuses_cached_record_and_does_not_call_provider(monkeypatch):
    cached_data = {
        "temp": 20.5,
        "description": "clear sky",
        "units": "celsius",
    }
    cached_record = SimpleNamespace(
        id=10,
        city_name="London",
        data=cached_data,
    )
    saved_record = SimpleNamespace(
        id=11,
        city_name="London",
        timestamp=datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        served_from_cache=True,
        data=cached_data,
    )
    repo_mock = Mock()
    repo_mock.get_cached_record = AsyncMock(return_value=cached_record)
    repo_mock.add_weather_query = AsyncMock(return_value=saved_record)

    provider_client_mock = Mock(side_effect=AssertionError("Provider should not be called"))
    monkeypatch.setattr("app.services.weather_service.AsyncClient", provider_client_mock)

    service = WeatherService(weather_repo=repo_mock)
    response = await service.get_weather("London", "celsius")

    repo_mock.get_cached_record.assert_awaited_once_with("London", "celsius")
    repo_mock.add_weather_query.assert_awaited_once_with(
        city="London",
        data=cached_data,
        served_from_cache=True,
    )
    provider_client_mock.assert_not_called()
    assert response == {
        "city_name": "London",
        "timestamp": datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
        "served_from_cache": True,
        "data": cached_data,
    }
