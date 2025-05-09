from fastapi import FastAPI, Request,status
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


# def register_rate_limit_err_handler(app:FastAPI):
#     @app.exception_handler(RateLimitExceeded)
#     async def on_rate_limit_err(request: Request, exc: RateLimitExceeded):
#         return JSONResponse(
#             status_code=status.HTTP_429_TOO_MANY_REQUESTS,
#             content={"detail": "Too many requests, please try again later."}
#         )