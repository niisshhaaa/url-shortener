from datetime import datetime
import logging,time
from fastapi import Request,status,Depends
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from backend.dependencies import get_session,get_session_factory
from backend.db_utils import get_idntier_api_key


# Configure Python’s logging to write to a file
logging.basicConfig(
    filename="request_logs.log",
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("request-logger")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Record arrival timestamp
        start_ts = datetime.now()
        start_timestamp = start_ts.isoformat()

        # 2. Let the request run
        response = await call_next(request)

        # 3. Record completion timestamp & compute duration
        end_ts = datetime.now()
        duration_ms = (end_ts - start_ts).total_seconds() * 1000

        # 4. Gather other details
        method = request.method
        url = str(request.url)
        ua = request.headers.get("user-agent", "unknown")
        ip = request.client.host if request.client else "unknown"

        # 5. Emit a single structured log line
        log_line = (
            f"[{start_timestamp}] "
            f"{ip} {method} {url} "
            f"UA={ua} "
            f"duration_ms={duration_ms:.2f}"
        )
        logger.info(log_line)
        print(log_line)  # For debugging purposes, you can also print to console

        return response



class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, session):
        super().__init__(app)
        self.session = session

    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("api-key")
        if not api_key:
            return JSONResponse(
                {"detail": "Missing API key"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        async with self.session() as session:
            identifier = await get_idntier_api_key(api_key, session)
            if not identifier:
                return JSONResponse(
                    {"detail": "Invalid API key"},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            
            request.state.user_id = identifier

        return await call_next(request)
