from datetime import datetime
import logging,time
from fastapi import HTTPException, Request, Response,status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from backend.url_shortener._cache import redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, ttl: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.ttl = ttl

    async def dispatch(self, request: Request, call_next):
       
        ip=request.client.host if request.client else None
        print("ip",ip)
        key = f"rate:{ip}"

        if ip :
            ip_counter=await redis_client.get(key)
            print("ip counter",ip_counter)
            

            # if ip key not in redis cache implies first request , set counter in redis with ttl of 1 min  
            if not ip_counter:
                counter=1
                await redis_client.set(key, counter, ex=self.ttl)
                
            # for requests after first request
            if ip_counter :
                ip_counter=int(ip_counter)
                counter=ip_counter+1
                if counter>=self.max_requests+1:
                    print("throttle")
                    return JSONResponse(
                        {"detail": "Rate limit exceeded. Try again later."},
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
                await redis_client.set(key, counter, ex=self.ttl)

        return await call_next(request)


