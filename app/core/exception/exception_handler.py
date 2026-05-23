from fastapi import Request
from fastapi.responses import JSONResponse 
from app.core.exception.exception import AppException

async def app_exception_handler(request: Request, exc: AppException):
    code = exc.code.value if hasattr(exc.code, "value") else exc.code

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
