
from fastapi.params import Header
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import  AsyncSession
from fastapi import Depends, HTTPException
from sqlalchemy import select
from db.dependencies import get_session
from backend.url_shortener.utils import  hash_code_without_entropy

from db.schema import  Users

from .repository import save_url,check_code_exists,retry_ifnot_unq,new_code_with_entropy


async def get_idntier_api_key(api_key,session):
    stmt=select(Users.id,Users.tier_level).where(Users.api_key==api_key)
    result=await session.execute(stmt)
    return result.first()

async def process_url(payload,session,user_id:int):
           
            valid_date=payload.exp_date

            if payload.custom_slug:
                short_code=payload.custom_slug
                code_exists=await check_code_exists(session,short_code)
                
                if code_exists:
                    if code_exists.original_url==payload.url_link and code_exists.user_id==user_id:
                        return {"original_url":code_exists.original_url,"short_url":code_exists.short_code,"password":code_exists.password}
                    
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Slug already exits, Retry")

                # attempt to save, catch IntegrityError in save_url for race cases     
                res=await save_url(session,user_id,original_url=payload.url_link,
                                        short_code=short_code,have_slug=True,exp_date=valid_date,password=payload.password)
                return {"original_url":res.original_url,"short_url":res.short_code,"password":res.password}
                
            # Non-custom slug path: deterministic code first    
            short_code=hash_code_without_entropy(payload.url_link,user_id)
            code_exists=await check_code_exists(session,short_code)
            print("code_exists",code_exists)
            
            if code_exists:
                if code_exists.user_id==user_id and code_exists.original_url==payload.url_link :
                    return {"original_url":code_exists.original_url,"short_url":code_exists.short_code,"password":code_exists.password}
                
                short_code=await new_code_with_entropy(payload.url_link,session)
            
            res=await save_url(session,user_id,original_url=payload.url_link,
                                        short_code=short_code,have_slug=False,exp_date=valid_date,password=payload.password)
            print('res',res)
            return {"original_url":res.original_url,"short_url":res.short_code,"password":res.password}


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




    