from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import AsyncClient
from sqlalchemy import text

from app.api.weather_api import router as weather_api_router
from app.config import settings
from app.core.exception.exception_handler import app_exception_handler
from app.core.exception.exception import AppException
from app.core.logging import configure_logging, get_logger
from app.db.session import engine


configure_logging(service_name="weather_api")
logger = get_logger(__name__)

app = FastAPI(
    title="Weather API",
    version="1.0.0"
)

app.include_router(weather_api_router)

app.add_exception_handler(AppException, app_exception_handler)

logger.info(
    "Application started",
    extra={"event": "app_started"},
)


@app.middleware("http")
async def log_request_lifecycle(request: Request, call_next):
    request_id = str(uuid4())
    started_at = perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    logger.info(
        "Request started",
        extra={
            "event": "request_started",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
        },
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.exception(
            "Request failed",
            extra={
                "event": "request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "duration_ms": duration_ms,
            },
        )
        raise

    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    logger.info(
        "Request finished",
        extra={
            "event": "request_finished",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": client_ip,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    return response


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
async def health(include_provider: bool = False):
    checks = {}
    status_code = 200

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = "error"
        status_code = 503
        logger.warning(
            "Health check failed",
            exc_info=True,
            extra={
                "event": "health_check_failed",
                "check": "database",
            },
        )

    if include_provider:
        try:
            async with AsyncClient(timeout=1.5) as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": "London",
                        "units": "metric",
                        "appid": settings.weather_api_key,
                    },
                )
                response.raise_for_status()
            checks["weather_provider"] = "ok"
        except Exception as exc:
            checks["weather_provider"] = "error"
            status_code = 503
            logger.warning(
                "Health check failed",
                exc_info=True,
                extra={
                    "event": "health_check_failed",
                    "check": "weather_provider",
                },
            )

    status = "ok" if status_code == 200 else "degraded"
    content = {
        "status": status,
        "checks": checks,
    }

    logger.info(
        "Health check completed",
        extra={
            "event": "health_check_completed",
            "status": status,
            "checks": checks,
            "include_provider": include_provider,
        },
    )

    if status_code != 200:
        return JSONResponse(status_code=status_code, content=content)

    return content

