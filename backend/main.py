from typing import Set
from config.blacklist import BLACKLIST_PATH, load_blacklist
from middlewares.middlewares import AuthorizationMiddleware, BlacklistMiddleware, LazyReloadBlacklistMiddleware, RequestLoggingMiddleware,AuthenticationMiddleware, TimingMiddleware
from db.db_connection import async_engine
from error_tracking.routes import sentry_router
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from prometheus.custom_instrumentator import instrumentator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from error_tracking.sentry_init import init_sentry
from db.db_connection import async_session
from backend.url_shortener.routes import urls_router
from backend.stats.routes import stats_router

blocked_keys: Set[str] = set()

version="v2"

version_prefix=f"/api/{version}"

@asynccontextmanager  
async def app_lifespan(app:FastAPI):

     await load_blacklist(blocked_keys)
     app.state.blocked_keys = blocked_keys
     app.state._last_mtime=BLACKLIST_PATH.stat().st_mtime

     # ORM only maps schema to python objects , so create the schema(tables) for deploying the api 
     # or add alembic update in start command of app service on deployed platform 
     
     # async with async_engine.begin() as conn:
     #      await conn.run_sync(Base.metadata.create_all)

     yield
    
     #resource disposal
     await async_engine.dispose()


# init_sentry()

app= FastAPI(lifespan=app_lifespan)

# app.state.limiter = limiter


# app.add_middleware(SlowAPIMiddleware)
# register_rate_limit_err_handler(app)

app.include_router(urls_router,prefix=f"{version_prefix}")
app.include_router(stats_router,prefix=f"{version_prefix}/stats")
# app.include_router(sentry_router)

app.add_middleware(AuthorizationMiddleware,paths=[f"{version_prefix}/shorten/batch"])
app.add_middleware(AuthenticationMiddleware, session=async_session,paths=[f"{version_prefix}/shorten", f"{version_prefix}/shorten/batch",f"{version_prefix}/shorten/" ,f"{version_prefix}/urls"])
app.add_middleware(LazyReloadBlacklistMiddleware)
# app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TimingMiddleware)


# app.add_middleware(SentryAsgiMiddleware)
# instrumentator.instrument(app).expose(app) 
# Instrumentator().instrument(app).expose(app) 
# adds a /metrics endpoint to app via which prometheus can scrape metrics







    





