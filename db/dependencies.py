from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import  AsyncSession
from .db_connection import async_session


#Scope of this will be to a specific route for a single specific request ,new session for each concurrent request when passed as dependency and using proper context scope.
async def get_session() -> AsyncGenerator[AsyncSession,None]:
    async with async_session() as session:  # using with context manager opens the session on first execute and closes the async session (sesion) instance at the end of with block
        yield session

async def get_session_factory():
    yield async_session