import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.client_ip import client_ip_from
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        requests: int = 60,
        window_seconds: int = 60,
        trusted_proxy_cidrs: list[str] | None = None,
        path_prefix: str | None = None,
    ) -> None:
        super().__init__(app)
        self.requests = requests
        self.window_seconds = window_seconds
        # Only honored when the socket peer is itself a trusted proxy (P3-11).
        self.trusted_proxy_cidrs = trusted_proxy_cidrs or []
        self.path_prefix = path_prefix
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        ip = client_ip_from(request, self.trusted_proxy_cidrs)
        return ip or "unknown"

    def _cleanup_old_requests(self, client_ip: str, now: float) -> None:
        window_start = now - self.window_seconds
        self._requests[client_ip] = [
            timestamp for timestamp in self._requests[client_ip] if timestamp > window_start
        ]
        # Bounded-memory strategy (P3-12): evict empty buckets and cap total
        # tracked IPs so unbounded unique sources cannot exhaust memory.
        if len(self._requests) > 10_000:
            for key in [k for k, v in self._requests.items() if not v][:5_000]:
                del self._requests[key]

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/api/v1/health"):
            return await call_next(request)

        # Path-scoped instances (e.g. stricter auth limits) only count their prefix.
        if self.path_prefix and not request.url.path.startswith(self.path_prefix):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()

        # Clean up old requests for this client
        self._cleanup_old_requests(client_ip, now)

        # Check if limit exceeded
        if len(self._requests[client_ip]) >= self.requests:
            retry_after = int(self.window_seconds - (now - self._requests[client_ip][0])) + 1
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Record this request
        self._requests[client_ip].append(now)

        response = await call_next(request)
        return response


def rate_limit_middleware_factory(
    requests: int | None = None,
    window_seconds: int | None = None,
) -> tuple[type[RateLimitMiddleware], dict[str, int]]:
    """Factory function to create middleware with configured settings."""
    requests = requests if requests is not None else settings.rate_limit_requests
    window_seconds = (
        window_seconds if window_seconds is not None else settings.rate_limit_window_seconds
    )
    return RateLimitMiddleware, {"requests": requests, "window_seconds": window_seconds}
