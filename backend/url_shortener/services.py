
from fastapi.params import Header
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import  AsyncSession

from datetime import datetime
import hashlib,random,socket,string
from typing import Optional
from urllib.parse import urlparse
from fastapi import Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import load_only
from backend.common.utils import check_is_date_valid
from db.dependencies import get_session
from backend.url_shortener.utils import hash_code_without_entropy, is_valid_url

from db.schema import URL_SHORTENER, Users

from .repository import save_url,check_code_exists,retry_ifnot_unq,check_url_exists


async def get_url(short_code:str,session:AsyncSession):
   
        result = await session.execute(
           select(URL_SHORTENER.short_code,URL_SHORTENER.deleted_at,URL_SHORTENER.expiry_date).where(URL_SHORTENER.short_code==short_code)
        )
        fetchresult=result.first()
        print(fetchresult)
        return fetchresult if fetchresult else None

async def url_to_update(short_code:str,session:AsyncSession):
   
        result = await session.execute(
           select(URL_SHORTENER.original_url,URL_SHORTENER.password,
                  URL_SHORTENER.expiry_date)
            # select(URL_SHORTENER
                #   )
                  .where(URL_SHORTENER.short_code==short_code)
        )
        # fetchresult=result.scalar()
        fetchresult=result.first()
        return fetchresult if fetchresult else None


    
async def get_idntier_api_key(api_key,session):
    stmt=select(Users.id,Users.tier_level).where(Users.api_key==api_key)
    result=await session.execute(stmt)
    return result.first()

async def process_url(payload,session,user_id:int):
            try:
                valid_date=payload.exp_date

                if payload.custom_slug:
                    short_code=payload.custom_slug
                    code_exists=await check_code_exists(session,short_code)
                    if code_exists:
                        if code_exists.original_url==payload.url_link and code_exists.user_id==user_id:
                            return {"original_url":code_exists.original_url,"short_url":code_exists.short_code,"pass":code_exists.password}
                        
                        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Slug already exits, Retry")
                         
                    res=await save_url(session,user_id,original_url=payload.url_link,
                                            short_code=short_code,have_slug=True,exp_date=valid_date,password=payload.password)
                    return {"original_url":res.original_url,"short_url":res.short_code,"pass":res.password}
                    
                short_code=hash_code_without_entropy(payload.url_link)
                code_exists=await check_code_exists(session,short_code)
                print("code_exists",code_exists)
                
                if code_exists:
                    if code_exists.original_url==payload.url_link and code_exists.user_id==user_id:
                        return {"original_url":code_exists.original_url,"short_url":code_exists,"pass":code_exists.password}
                    
                    short_code=await retry_ifnot_unq(short_code,payload.url_link,session)
                
                res=await save_url(session,user_id,original_url=payload.url_link,
                                            short_code=short_code,have_slug=False,exp_date=valid_date,password=payload.password)
                print('res',res)
                return {"original_url":res.original_url,"short_url":res.short_code,"pass":res.password}

            except HTTPException:
                raise    

            except Exception as e:
                raise HTTPException(status_code=500,detail=str(e))

async def check_api_key(api_key:str=Header(...),session: AsyncSession = Depends(get_session)):
    if not api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    
    idntier=await get_idntier_api_key(api_key,session)

    if not idntier:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not a valid api key")
    return idntier



async def get_id_api_key(api_key,session):
    stmt=select(Users.id).where(Users.api_key==api_key)
    result=await session.execute(stmt)
    return result.first() if result else None 




    