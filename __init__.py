from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.middleware import SlowAPIMiddleware
from middlewares.middlewares import RequestLoggingMiddleware
from middlewares.conditional_middlewares import ConditionalLoggingMiddleware
from db.conn_session import async_engine
from backend.main_new import urls_router
from error_tracking.routes import sentry_router
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from backend.rate_limit_utils import limiter
# from global_exceptions.rate_limit_exception import register_rate_limit_err_handler
from prometheus.custom_instrumentator import instrumentator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from error_tracking.sentry_init import init_sentry
# from prometheus_fastapi_instrumentator import Instrumentator

@asynccontextmanager  
async def app_lifespan(app:FastAPI):

     # ORM only maps schema to python objects , so create the schema(tables) for deploying the api 
     # or add alembic update in start command of app service on deployed platform 
     
     # async with async_engine.begin() as conn:
     #      await conn.run_sync(Base.metadata.create_all)

     yield
    
     #resource disposal
     await async_engine.dispose()


init_sentry()

app= FastAPI(lifespan=app_lifespan)

# app.state.limiter = limiter


# app.add_middleware(SlowAPIMiddleware)
# register_rate_limit_err_handler(app)

app.include_router(urls_router)
app.include_router(sentry_router)
# app.add_middleware(RequestLoggingMiddleware) 

app.add_middleware(ConditionalLoggingMiddleware, paths=[])

# app.add_middleware(SentryAsgiMiddleware)
instrumentator.instrument(app).expose(app) 
# Instrumentator().instrument(app).expose(app) 
# adds a /metrics endpoint to app via which prometheus can scrape metrics
    








