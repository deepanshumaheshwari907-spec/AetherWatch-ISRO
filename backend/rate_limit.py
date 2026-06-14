import threading
import time
from collections import defaultdict, deque

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

_rl_logger = logging.getLogger("backend.rate_limit")
import os
from config import Config


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Small single-instance limiter; the reverse proxy remains the outer guard."""

    def __init__(self, app, public_per_minute=120, admin_per_minute=10):
        super().__init__(app)
        self.public_limit = public_per_minute
        self.admin_limit = admin_per_minute
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()

    async def dispatch(self, request, call_next):
        forwarded = request.headers.get("x-forwarded-for", "")
        client_ip = forwarded.split(",")[0].strip()
        if not client_ip and request.client:
            # request.client can be an object with `host` attr or a (host, port) tuple
            client = request.client
            if hasattr(client, "host"):
                client_ip = client.host
            else:
                try:
                    client_ip = client[0]
                except Exception:
                    client_ip = ""
        client_ip = client_ip or "unknown"
        is_admin = request.url.path.startswith("/api/v1/admin/")
        limit = self.admin_limit if is_admin else self.public_limit
        key = (client_ip, "admin" if is_admin else "public")
        now = time.monotonic()
        try:
            with self.lock:
                timestamps = self.requests[key]
                while timestamps and now - timestamps[0] >= 60:
                    timestamps.popleft()
                if len(timestamps) >= limit:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                        headers={"Retry-After": "60"},
                    )
                timestamps.append(now)
        except Exception as exc:
            # Defensive logging to capture the problematic state for debugging
            ts = self.requests.get(key, None)
            _rl_logger.exception(
                "RateLimitMiddleware error: key=%s ts_type=%s ts_repr=%r",
                key,
                type(ts),
                ts,
            )
            # Fallback: write a small debug file with the captured state
            try:
                debug_path = os.path.join(os.path.dirname(Config.LOG_FILE), "rate_limit_debug.txt")
                with open(debug_path, "a", encoding="utf-8") as fh:
                    fh.write(f"TIME={time.time()} KEY={key} TS_TYPE={type(ts)} TS_REPR={repr(ts)}\n")
            except Exception:
                pass
            raise
        return await call_next(request)
