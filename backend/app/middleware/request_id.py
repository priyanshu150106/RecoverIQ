"""Correlation / Request ID Middleware for RecoverIQ.

Assigns a unique correlation ID (UUID4) to each incoming HTTP request,
propagates it across loggers, and attaches 'X-Request-ID' to response headers.
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that injects and propagates X-Request-ID header."""

    async def dispatch(self, request: Request, call_next):
        # 1. Check existing X-Request-ID or generate new UUID
        request_id = request.headers.get("X-Request-ID")
        if not request_id or not request_id.strip():
            request_id = str(uuid.uuid4())

        # 2. Attach to request state for downstream handlers and logger
        request.state.request_id = request_id

        # 3. Process request
        response: Response = await call_next(request)

        # 4. Attach X-Request-ID to response header
        response.headers["X-Request-ID"] = request_id
        return response
