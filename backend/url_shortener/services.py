
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

from .repository import save_url,check_code_exists,retry_ifnot_unq


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

async def process_url(payload,session,get_user_id_reqst):
            try:
                valid_date=payload.exp_date
                user_id_reqst=get_user_id_reqst.id

                if payload.custom_slug:
                    slug_code=payload.custom_slug
                    code_exists=await check_code_exists(session,slug_code)
                    if code_exists:
                        raise HTTPException(status_code=409,detail="Slug already exits, Retry")
                    short_code=slug_code
                    newinsert=await save_url(session,user_id_reqst,original_url=payload.url_link,
                                             short_code=short_code,have_slug=True,exp_date=valid_date,password=payload.password)
                    print('newinsert',newinsert)
                    response={"original_url":newinsert.original_url,"short_url":newinsert.short_code,"pass":newinsert.password}
                else:
                    hash_code=hash_code_without_entropy(payload.url_link)
                    code_exists=await check_code_exists(session,hash_code)
                    print("code_exists",code_exists)
                    code_exists_scode=code_exists.short_code if code_exists else None
                    
                    if code_exists_scode:
                        if code_exists.original_url==payload.url_link and code_exists.user_id==user_id_reqst:
                            short_code=hash_code
                            response={"original_url":code_exists.original_url,"short_url":short_code}
                        else:
                            short_code=await retry_ifnot_unq(hash_code,payload.url_link,session)

                            newinsert= await save_url(session,user_id_reqst,original_url=payload.url_link,
                                                  short_code=short_code,have_slug=False,
                                                  exp_date=valid_date,password=payload.password)
                            print('newinsert',newinsert)
                            response={"original_url":newinsert.original_url,"short_url":newinsert.short_code,"pass":newinsert.password}
                        
                    else:
                        short_code=hash_code
                        newinsert=await save_url(session,user_id_reqst,original_url=payload.url_link,
                                                 short_code=short_code,have_slug=False,exp_date=valid_date,password=payload.password)
                        print('newinsert',newinsert)
                        response={"original_url":newinsert.original_url,"short_url":newinsert.short_code,"pass":newinsert.password}
                
                return response

            except Exception as e:
                 return {"url":payload.url_link,"short_code":None,"error":e}

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




    