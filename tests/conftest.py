import httpx
import pytest_asyncio

from app.main import app


@pytest_asyncio.fixture
async def simple_async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client
