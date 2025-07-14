from datetime import datetime
import logging,time
from fastapi import Request,status,Depends
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from .dependencies import get_session
from .db_utils import get_idntier_api_key

logging.basicConfig(
    filename="request_logs.log",
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("request-logger")

# class RequestLoggingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request, call_next):
#         start_time=time.perf_counter()
#         response=await call_next(request)
#         end_time=time.perf_counter()
#         process_time=end_time-start_time
#         message=f'{request.client.host}:{request.client.port} - "{request.method}{request.url.path}" {response.status_code} took {process_time} '
#         # logger.info(message)
#         print (message)
#         return response
    

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


# class AuthenticationMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request:Request, call_next:RequestResponseEndpoint,db_session=get_session):
#         api_key=request.headers.get("api-key")

#         if not api_key:
#              return JSONResponse(content={"detail": "Missing API key"},status_code=status.HTTP_401_UNAUTHORIZED)
        
#         session_factory = request.app.state.async_session
        
#         async with session_factory() as db_session:
#             try:
#                idntier=await get_idntier_api_key(api_key,db_session)
#                request.state.idntier=idntier
#             except Exception as e:
#                logger.error(f"Authentication failed: {str(e)}")
#                return JSONResponse(content={"detail": "Invalid API key"},status_code=status.HTTP_401_UNAUTHORIZED)
        
#         return await call_next(request)
