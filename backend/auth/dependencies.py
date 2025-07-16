from fastapi.security import HTTPBearer, http
from fastapi import Request,status,HTTPException
from ..url_shortener.utils import decode_token
from abc import ABC,abstractmethod
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import  AsyncSession
from db.db_connection import async_session

#* set auto_erro to false later
class Authentication(HTTPBearer):
    def __init__(self,auto_error=False):
        HTTPBearer.__init__(self,auto_error=auto_error)
    
    async def __call__(self,request:Request)->http.HTTPAuthorizationCredentials|None:
        auth=await HTTPBearer.__call__(self,request)
        key=auth.credentials if auth else None

        return key
        