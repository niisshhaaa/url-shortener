import datetime
import logging
from fastapi import Request, logger
from starlette.middleware.base import BaseHTTPMiddleware

# Configure Python’s logging to write to a file
logging.basicConfig(
    filename="request_logs.log",
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("request-logger")

class ConditionalLoggingMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, *args, paths: list[str], **kwargs):
        self.paths = paths
        super().__init__(app, *args, **kwargs)

    async def dispatch(self, request: Request, call_next = None):
        if not any(request.url.path.startswith(p) for p in self.paths):

            # 1. Record arrival timestamp
            start_ts = datetime.datetime.now()
            start_timestamp = start_ts.isoformat()

            # 2. Let the request run
            response = await call_next(request)

            # 3. Record completion timestamp & compute duration
            end_ts = datetime.datetime.now()
            duration_ms = (end_ts - start_ts).total_seconds() * 1000

            # 4. Gather other details
            method, url = request.method, str(request.url)
            ua = request.headers.get("user-agent", "unknown")
            ip = request.client.host if request.client else "unknown"

            # 5. Emit a single structured log line
            log_line = f"[{start_timestamp}]{ip} {method} {url} UA={ua} duration_ms={duration_ms:.2f}"
            logger.info(log_line)
            print(log_line)  # For debugging purposes, you can also print to console

            return response