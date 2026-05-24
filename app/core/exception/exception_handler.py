from fastapi import Request
from fastapi.responses import JSONResponse 
from app.core.exception.exception import AppException
from app.core.logging import get_logger


logger = get_logger(__name__)

async def app_exception_handler(request: Request, exc: AppException):
    code = exc.code.value if hasattr(exc.code, "value") else exc.code
    log_method = logger.warning if exc.status_code < 500 else logger.error

    log_method(
        "Application exception handled",
        exc_info=(type(exc), exc, exc.__traceback__) if exc.status_code >= 500 else None,
        extra={
            "event": "app_exception_handled",
            "status_code": exc.status_code,
            "error_code": code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )
