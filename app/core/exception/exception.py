from datetime import date

from app.core.exception.exception_enum import ExceptionCode

class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        code: ExceptionCode,
        message: str,
        details: dict | None = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class WeatherProviderError(AppException):
    def __init__(self, city_name: str):
        super().__init__(
            status_code=502,
            code=ExceptionCode.WEATHER_PROVIDER_ERROR,
            message="Weather provider is unavailable. Please try again later.",
            details={"city_name": city_name}
        )


class CityNotFoundError(AppException):
    def __init__(self, city_name: str):
        super().__init__(
            status_code=404,
            code=ExceptionCode.CITY_NOT_FOUND,
            message=f"City {city_name} was not found.",
            details={"city_name": city_name}
        )

    
class WeatherProviderAuthError(AppException):
    def __init__(self):
        super().__init__(
            status_code=502,
            code=ExceptionCode.WEATHER_PROVIDER_AUTH_ERROR,
            message="Weather provider authentication failed.",
            details={}
        )


class WeatherResponseFormatError(AppException):
    def __init__(self):
        super().__init__(
            status_code=502,
            code=ExceptionCode.WEATHER_RESPONSE_FORMAT_ERROR,
            message="Unexpected weather provider response format.",
            details={}
        )


class WeatherStorageError(AppException):
    def __init__(self):
        super().__init__(
            status_code=500,
            code=ExceptionCode.WEATHER_STORAGE_ERROR,
            message="Could not save or load weather data.",
            details={}
        )


class InvalidHistoryRangeError(AppException):
    def __init__(self, date_from: date, date_to: date):
        super().__init__(
            status_code=400,
            code=ExceptionCode.INVALID_HISTORY_RANGE,
            message="date_from must be less than or equal to date_to.",
            details={
                "date_from": str(date_from),
                "date_to": str(date_to)
            }
        )















