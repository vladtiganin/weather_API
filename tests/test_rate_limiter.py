from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from app.core import dependencies
from app.core.rate_limiter import rate_limiter
from app.main import app


@pytest.mark.asyncio
async def test_rate_limit_returns_429_and_prevents_service_call_after_limit(
    simple_async_client: httpx.AsyncClient,
):
    service_mock = Mock()
    service_mock.get_weather = AsyncMock(
        return_value={
            "city_name": "London",
            "timestamp": datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc),
            "served_from_cache": False,
            "data": {
                "temp": 21.0,
                "description": "clear sky",
                "units": "celsius",
            },
        }
    )
    original_max_requests = rate_limiter.max_requests
    original_window_seconds = rate_limiter.window_seconds
    rate_limiter.max_requests = 1
    rate_limiter.window_seconds = 60
    rate_limiter.requests.clear()
    app.dependency_overrides[dependencies.get_weather_service_instance] = (
        lambda: service_mock
    )

    try:
        first_response = await simple_async_client.get(
            "/weather",
            params={"city": "London", "unit": "celsius"},
        )
        second_response = await simple_async_client.get(
            "/weather",
            params={"city": "London", "unit": "celsius"},
        )
    finally:
        app.dependency_overrides.clear()
        rate_limiter.requests.clear()
        rate_limiter.max_requests = original_max_requests
        rate_limiter.window_seconds = original_window_seconds

    service_mock.get_weather.assert_awaited_once_with("London", "celsius")
    assert first_response.status_code == 200
    assert second_response.status_code == 429
    assert second_response.json()["error"]["code"] == "TOO_MANY_REQUESTS"
