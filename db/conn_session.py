from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession ,async_sessionmaker
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager 
from db.schema import Base



load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# DATABASE_URL format : "postgresql+asyncpg://user:password@localhost/URL_SHORTENER"

#Create async database engine
async_engine=create_async_engine(DATABASE_URL,future=True, echo=True,
                                      pool_size=20,max_overflow=30)
#create an async session factory using engine for connection
async_session=async_sessionmaker(bind=async_engine,class_=AsyncSession,expire_on_commit=False)











          
        
