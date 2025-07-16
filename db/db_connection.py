from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession ,async_sessionmaker
from config.config import configSettgs


DATABASE_URL = configSettgs.DATABASE_URL

# DATABASE_URL format : "postgresql+asyncpg://user:password@localhost/URL_SHORTENER"

#Create async database engine connection
async_engine=create_async_engine(DATABASE_URL,future=True, echo=True,
                                      pool_size=20,max_overflow=30)

#Create an async session factory using engine for connection
async_session=async_sessionmaker(bind=async_engine,class_=AsyncSession,expire_on_commit=False)











          
        
