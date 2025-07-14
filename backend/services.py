
from fastapi.params import Header
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import hashlib,random,socket,string
from typing import Optional
from urllib.parse import urlparse
from fastapi import Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import load_only


from backend.dependencies import get_session
from backend.utils import is_valid_url
from backend.utils import check_is_date_valid, hash_code_with_entropy, hash_code_without_entropy, random_code
from db.schema import URL_SHORTENER, Users


async def check_code_exists(session,short_code:str):
    result = await session.execute(
       select(URL_SHORTENER.original_url,URL_SHORTENER.short_code,URL_SHORTENER.user_id).where(URL_SHORTENER.short_code==short_code)
    )
    res=result.first()
    return res if res else None


async def retry_ifnot_unq(short_code:str,url,session):
    
    max_attempts = 5
    attempts = 0
    while True:
        hash_code_new = hashlib.md5(f"{url}{attempts}".encode()).hexdigest()[:6]
        code_exists=await check_code_exists(session,hash_code_new) 
        code_exists_scode=code_exists.URL_SHORTENER.short_code if code_exists else None 
        if not code_exists_scode:
            break
        attempts+=1

       

        if attempts>=max_attempts:
            raise HTTPException(status_code=500,detail='couldn''t generate unique code')
        
        
    short_code=hash_code_new
    return short_code

async def save_url(session,userid,original_url:str,short_code:str,have_slug:bool,exp_date:Optional[datetime]=None,password:Optional[str]=None):  
   
    new_urlncode=URL_SHORTENER(original_url=original_url,short_code=short_code,user_id=userid,expiry_date=exp_date,password=password)
    session.add(new_urlncode)  # Session.add()' operation is not currently supported within the execution stage of the flush process. Results may not be consistent.  Consider using alternative event listeners or connection-level operations instead.
    try:
        await session.commit()
        await session.refresh(new_urlncode)
        return new_urlncode
    except IntegrityError:
        await session.rollback()

        code_exists=await check_code_exists(session,short_code)

        if code_exists and have_slug:
            raise HTTPException(status_code=409,detail="Slug already exits, Retry")

        if code_exists.short_code:
            if code_exists.original_url==original_url and code_exists.user_id==userid:
               return new_urlncode
            else:
               short_code=await retry_ifnot_unq(short_code,original_url,session)
               newinsert= await save_url(session,original_url,short_code)
               return newinsert
    except Exception as e:
        await session.rollback()
        raise e
        
        
    

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

async def load_url(short_code:str,session:AsyncSession):
   
        result = await session.execute(
           select(URL_SHORTENER)
           .where(URL_SHORTENER.short_code == short_code))
        res=result.scalar_one_or_none()
        print(res)
        return res if res else None



async def retry_ifnot_unq(short_code:str,url,session):
    
    max_attempts = 5
    attempts = 0
    while True:
        hash_code_new = hash_code_with_entropy(url)+random_code()
        code_exists=await check_code_exists(session,hash_code_new) 
        code_exists_scode=code_exists.short_code if code_exists else None 
        if not code_exists_scode:
            break
        attempts+=1

        if attempts>=max_attempts:
            raise HTTPException(status_code=500,detail='couldn''t generate unique code')
        
    short_code=hash_code_new
    return short_code
    
async def get_idntier_api_key(api_key,session):
    stmt=select(Users.id,Users.tier_level).where(Users.api_key==api_key)
    result=await session.execute(stmt)
    return result.first()

async def process_url(payload,session,get_user_id_reqst):
            try:
                if not is_valid_url(payload.url_link):
                    raise HTTPException(
                    status_code=400, detail="Invalid or insecure URL format")
            
                valid_date=None
                if payload.exp_date:
                    valid_date=check_is_date_valid(payload.exp_date)
                
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

async def del_scode(session,short_code):
    # await session.execute(delete(URL_SHORTENER).where(URL_SHORTENER.short_code==short_code))
    stmt=(
        update(URL_SHORTENER)
        .where(URL_SHORTENER.short_code==short_code)
        .values(deleted_at=datetime.now())
        .returning(URL_SHORTENER.deleted_at)
    )
    result=await session.execute(stmt)
    result=result.first()
    print("deleted result",result)
    await session.commit()
    return result

async def get_id_api_key(api_key,session):
    stmt=select(Users.id).where(Users.api_key==api_key)
    result=await session.execute(stmt)
    return result.first() if result else None 

async def get_userid_scode(scode,session):
    stmt=select(URL_SHORTENER.user_id,URL_SHORTENER.deleted_at).where(URL_SHORTENER.short_code==scode)
    result=await session.execute(stmt)
    print("scode res",result)
    return result.first() if result else None # will return None in case when short code does not exist , (None,) if user id is null while only retrieving user_id

async def del_scode(session,short_code):
    await session.execute(delete(URL_SHORTENER).where(URL_SHORTENER.short_code==short_code))
    await session.commit()
    