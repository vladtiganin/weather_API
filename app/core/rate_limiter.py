from collections import defaultdict, deque
from time import time
from fastapi import Request, status
from app.config import settings
from app.core.exception.exception import TooManyRequestsError


class RateLiimter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)


    def is_allowed(self, client_ip: str) -> bool:
        now = time()
        window_start = now - self.window_seconds

        request_times = self.requests[client_ip]

        while request_times and request_times[0] <= window_start:
            request_times.popleft()

        if len(request_times) >= self.max_requests:
            return False
        
        request_times.append(now)
        return True
    

rate_limiter = RateLiimter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds
)


async def rate_limit_by_ip(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_ip):
        raise TooManyRequestsError()

