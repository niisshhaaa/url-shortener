from datetime import datetime
import logging,time
from fastapi import HTTPException, Request, Response,status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from backend.common.repository import get_idntier_api_key
from backend.auth.dependencies import Authentication
from config.blacklist import BLACKLIST_PATH, load_blacklist


# Configure Python’s logging to write to a file
logging.basicConfig(
    filename="request_logs.log",
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("request-logger")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Record arrival timestamp
        start_ts = datetime.now()
        start_timestamp = start_ts.isoformat()

        response = await call_next(request)

        #  Gather other details
        method = request.method
        url = str(request.url)
        ua = request.headers.get("user-agent", "unknown")
        ip = request.client.host if request.client else "unknown"

        # 5. Emit a single structured log line
        log_line = (
            f"[{start_timestamp}] "
            f"{ip} {method} {url} "
            f"UA={ua} "
        )
        logger.info(log_line)

        return response



class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, session,paths: list[str]):
        super().__init__(app)
        self.session = session
        self.paths = paths


    async def dispatch(self, request: Request, call_next):
        if not any(request.url.path.startswith(p) for p in self.paths):
            # Skip authentication for paths that don't require it
            return await call_next(request)
       
        api_key = await Authentication()(request)
    
        if not api_key:
            return JSONResponse(
                {"detail": "Missing or Invalid Auth Headers"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        async with self.session() as session:
            identifier = await get_idntier_api_key(api_key, session)
            if not identifier:
                return JSONResponse(
                    {"detail": "Invalid API key"},
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Attach the identifier to the request state to use in other middlewares
            request.state.user_identifier = identifier


        return await call_next(request)
    

class AuthorizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *args, paths: list[str], **kwargs):
        self.paths = paths
        super().__init__(app, *args, **kwargs)
    
    async def dispatch(self, request: Request, call_next):

        if not any(request.url.path.startswith(p) for p in self.paths):
            # Skip authentication for paths that don't require it
            return await call_next(request)

        identifier = request.state.user_identifier

        if identifier.tier_level != 'ENTERPRISE':
            return JSONResponse(
                {"detail": "Invalid request for Hobby tier without pricing"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
            
        return await call_next(request)


class BlacklistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
       
        # considering if usually IP's blocked, so retreiving api_key seprately from Authorization headers
        api_key = request.headers.get("api-key", "")
        
        if  api_key in request.app.state.blocked_keys:
            return JSONResponse(
                {"detail": "Please try after some time"},
                status_code=status.HTTP_403_FORBIDDEN
            )
        return await call_next(request)
    

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
      
        # 1. Record start time in ns
        start_ns = time.perf_counter_ns()

        # 2. Process the request
        response: Response = await call_next(request)

        # 3. Record end time and compute elapsed
        end_ns = time.perf_counter_ns()
        elapsed_ns = end_ns - start_ns
        elapsed_ms = elapsed_ns / 1_000_000  # convert to milliseconds

        # 4. Add to response headers
        response.headers["X-Process-Time"] = f"{elapsed_ms:.3f}"

        return response
    

class LazyReloadBlacklistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        
    async def _reload_from_disk(self,app_state):
        """
        Only re-read the JSON if the mtime has changed,
        but do that file-read asynchronously.
        """
        try:
            mtime = BLACKLIST_PATH.stat().st_mtime
        except FileNotFoundError:
            mtime = 0.0

        if mtime and mtime > app_state._last_mtime:
            print("reload happening")
            await load_blacklist(app_state.blocked_keys)
            app_state._last_mtime = mtime

    async def dispatch(self, request: Request, call_next):

        
        app_state=request.app.state
        
        await self._reload_from_disk(app_state)
       
        # considering if usually IP's blocked, so retreiving api_key seprately from Authorization headers
        api_key = request.headers.get("api-key", "")
        
        if  api_key in request.app.state.blocked_keys:
            return JSONResponse(
                {"detail": "Please try after some time"},
                status_code=status.HTTP_403_FORBIDDEN
            )
        return await call_next(request)