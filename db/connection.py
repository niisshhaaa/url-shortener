from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine,AsyncEngine
from sqlalchemy.exc import SQLAlchemyError
import os,sys
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI

load_dotenv()

# logging.basicConfig(level=logging.INFO)  # You can change the level to INFO, WARNING, etc.
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
# DATABASE_URL format : "postgresql://user:password@localhost/URL_SHORTENER"



# async def get_db_connection():
#     try:
#         async with engine.connect() as conn:
#             logger.info("Wohoo connected !!")
#             yield conn #use yield as conn will be used as a dependency
#     except SQLAlchemyError as e:
#         logger.error(f"SQLAlchemyError occurred: {e}")
#         raise  # Propagate the error
#     except Exception as e:
#          # Handle any other unforeseen exceptions
#         logger.error(f"Unexpected error occurred: {e}")
#         raise  # Re-raise the exception after logging it to propagate errors 
#     finally:
#         await conn.close()  
        # context manager of python (use of with) will automatically close the connection at the end of with block
        # so it's really not required to close it in finally and add finally and except clauses.
        # with this method of building connection transaction will autobegin on first .execute and will be active until .commit / . rollback called
        # although after transaction end it will wait for .execute if any are there until the scope ends and then finally close.

# Dependency for database connection




# get_db_connection()

@asynccontextmanager
async def app_lifespan(app:FastAPI):
     #Create async database engine
     async_engine=create_async_engine(DATABASE_URL,future=True, echo=True)
    #  async_conn=async_engine.connect()

     app.state.engine=async_engine
    #  app.state.connection=async_conn
     
     yield
     
     #resource disposal
     await async_engine.dispose()

def create_app() -> FastAPI:
    app= FastAPI(lifespan=app_lifespan)
    return app