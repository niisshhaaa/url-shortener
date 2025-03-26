import sys,asyncio

if sys.platform=='win32':
          asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession ,async_sessionmaker
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager 
from db.schema import Base


load_dotenv()

# logging.basicConfig(level=logging.INFO)  # You can change the level to INFO, WARNING, etc.
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# DATABASE_URL format : "postgresql+asyncpg://user:password@localhost/URL_SHORTENER"


@asynccontextmanager
async def app_lifespan(app:FastAPI):
     #Create async database engine
     async_engine=create_async_engine(DATABASE_URL,future=True, echo=True)
     #create an async session factory using engine for connection
     async_session=async_sessionmaker(bind=async_engine,class_=AsyncSession,expire_on_commit=False)
     
     #resource initialisation , attach to app state to make it globally avbl and to use it later
     app.state.engine=async_engine
     app.state.async_session=async_session
     
     #Not required for running app locally(as schema with data is already created on device) 
     #ORM only maps schema to python objects , so create the schema(tables) for deploying the api 
     # async with async_engine.begin() as conn:
     #      await conn.run_sync(Base.metadata.create_all)

     yield
     
     #resource disposal
     await async_engine.dispose()


def create_app() -> FastAPI:
    app= FastAPI(lifespan=app_lifespan)
    return app

#redeploy
















          
        
