"""Origin enforcement for cookie-authenticated state-changing requests (P3-10).

Defense-in-depth layered on SameSite=Lax session cookies: any unsafe request
that *carries* a session cookie and presents an Origin/Referer that is not an
allowed origin is rejected with 403. Absent Origin/Referer is permitted —
same-origin browser requests always send Origin, and non-browser clients
(bearer-token Android) carry no session cookie and skip the check entirely.
"""

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

UNSAFE_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})


class CSRFOriginMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, allowed_origins: list[str], cookie_name: str) -> None:
        super().__init__(app)
        self.allowed_origins = set(allowed_origins)
        self.cookie_name = cookie_name

    @staticmethod
    def _request_origin(request: Request) -> str | None:
        origin = request.headers.get("origin")
        if origin:
            return origin.rstrip("/")
        referer = request.headers.get("referer")
        if referer:
            # Referer is an absolute URL; take scheme://host[:port]
            from urllib.parse import urlsplit

            parts = urlsplit(referer)
            if parts.netloc:
                return f"{parts.scheme}://{parts.netloc}"
        return None

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        if request.method in UNSAFE_METHODS and request.cookies.get(self.cookie_name):
            origin = self._request_origin(request)
            if origin and origin not in self.allowed_origins:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Cross-origin request rejected",
                        "error_code": "CSRF_ORIGIN_REJECTED",
                    },
                )
        return await call_next(request)
