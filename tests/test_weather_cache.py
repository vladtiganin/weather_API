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


@pytest.mark.asyncio
async def test_get_weather_fetches_fresh_record_when_cache_misses(monkeypatch):
    provider_response = Mock()
    provider_response.status_code = 200
    provider_response.raise_for_status = Mock()
    provider_response.json = Mock(
        return_value={
            "weather": [{"description": "light rain"}],
            "main": {"temp": 18.2},
        }
    )

    provider_clients = []

    class ProviderClientMock:
        def __init__(self):
            self.get = AsyncMock(return_value=provider_response)
            provider_clients.append(self)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

    fresh_data = {
        "temp": 18.2,
        "description": "light rain",
        "units": "celsius",
    }
    saved_record = SimpleNamespace(
        id=12,
        city_name="London",
        timestamp=datetime(2026, 5, 24, 12, 5, tzinfo=timezone.utc),
        served_from_cache=False,
        data=fresh_data,
    )
    repo_mock = Mock()
    repo_mock.get_cached_record = AsyncMock(return_value=None)
    repo_mock.add_weather_query = AsyncMock(return_value=saved_record)

    monkeypatch.setattr("app.services.weather_service.AsyncClient", ProviderClientMock)

    service = WeatherService(weather_repo=repo_mock)
    response = await service.get_weather("London", "celsius")

    repo_mock.get_cached_record.assert_awaited_once_with("London", "celsius")
    repo_mock.add_weather_query.assert_awaited_once_with(
        city="London",
        data=fresh_data,
    )
    assert len(provider_clients) == 1
    provider_clients[0].get.assert_awaited_once()
    assert provider_clients[0].get.await_args.kwargs["params"]["q"] == "London"
    assert provider_clients[0].get.await_args.kwargs["params"]["units"] == "metric"
    assert response == {
        "city_name": "London",
        "timestamp": datetime(2026, 5, 24, 12, 5, tzinfo=timezone.utc),
        "served_from_cache": False,
        "data": fresh_data,
    }
