from datetime import datetime
import hashlib
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import  select, update ,delete
from db.schema import URL_SHORTENER

async def load_url(short_code:str,session:AsyncSession):
   
        result = await session.execute(
           select(URL_SHORTENER)
           .where(URL_SHORTENER.short_code == short_code))
        res=result.scalar_one_or_none()
        print(res)
        return res if res else None

async def get_userid_scode(scode,session):
    stmt=select(URL_SHORTENER.user_id,URL_SHORTENER.deleted_at).where(URL_SHORTENER.short_code==scode)
    result=await session.execute(stmt)
    print("scode res",result)
    return result.first() if result else None # will return None in case when short code does not exist , (None,) if user id is null while only retrieving user_id


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

async def del_scode(session,short_code):
    await session.execute(delete(URL_SHORTENER).where(URL_SHORTENER.short_code==short_code))
    await session.commit()

async def check_code_exists(session,short_code:str):
    result = await session.execute(
       select(URL_SHORTENER.original_url,URL_SHORTENER.short_code,URL_SHORTENER.user_id,URL_SHORTENER.password).where(URL_SHORTENER.short_code==short_code)
    )
    res=result.first()
    print("codeexists",res)
    return res 

async def check_url_exists(session,short_code:str):
    result = await session.execute(
       select(URL_SHORTENER.original_url,URL_SHORTENER.short_code).where(URL_SHORTENER.short_code==short_code)
    )
    res=result.first()
    print("codeexists",res)
    return res 

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
            raise HTTPException(status_code=500,detail='Couldn''t generate unique short code,try custom code')
        
        
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
        
        