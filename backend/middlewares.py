import logging,time
from fastapi import Request,status,Depends
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
from .dependencies import get_session
from .db_utils import get_idntier_api_key

logger=logging.getLogger("app")

class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time=time.perf_counter()
        response=await call_next(request)
        end_time=time.perf_counter()
        process_time=end_time-start_time
        message=f'{request.client.host}:{request.client.port} - "{request.method}{request.url.path}" {response.status_code} took {process_time:.4f} seconds'
        # logger.info(f"Request{request.url.path} took ")
        print(message)
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next:RequestResponseEndpoint,db_session=get_session):
        api_key=request.headers.get("api-key")

        if not api_key:
             return JSONResponse(content={"detail": "Missing API key"},status_code=status.HTTP_401_UNAUTHORIZED)
        
        session_factory = request.app.state.async_session
        
        async with session_factory() as db_session:
            try:
               idntier=await get_idntier_api_key(api_key,db_session)
               request.state.idntier=idntier
            except Exception as e:
               logger.error(f"Authentication failed: {str(e)}")
               return JSONResponse(content={"detail": "Invalid API key"},status_code=status.HTTP_401_UNAUTHORIZED)
        
        return await call_next(request)
