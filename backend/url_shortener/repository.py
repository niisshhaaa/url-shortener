import asyncio
from datetime import datetime
import hashlib
import random
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, func, select, update
from backend.cache.services import  update_short_code_cache
from db.schema import URL_SHORTENER
from db.db_connection import async_session


async def load_url(session:AsyncSession,short_code:str):

        result = await session.execute(
           select(
            URL_SHORTENER.original_url,
            URL_SHORTENER.password,
            URL_SHORTENER.expiry_date,
            URL_SHORTENER.updated_at
            )
           .where(URL_SHORTENER.short_code == short_code,
           URL_SHORTENER.deleted_at.is_(None)))
        res=result.one_or_none()
        res = {
                "original_url": res.original_url,
                "password": res.password,
                "expiry_date": res.expiry_date,
                "updated_at":res.updated_at 
        }
        return res 

async def get_userid_scode(scode,session):
    stmt=select(URL_SHORTENER.user_id,URL_SHORTENER.password,URL_SHORTENER.short_code).where(URL_SHORTENER.short_code==scode,URL_SHORTENER.deleted_at.is_(None))
    result=await session.execute(stmt)
    return result.first() if result else None


async def check_code_exists(session,short_code:str):
    result = await session.execute(
       select(URL_SHORTENER.original_url,URL_SHORTENER.short_code,URL_SHORTENER.user_id,URL_SHORTENER.password).
       where(URL_SHORTENER.short_code==short_code,
             URL_SHORTENER.deleted_at.is_(None))
    )
    res=result.first()
    return res 


async def new_code_with_entropy(url,session,min_length=5,max_length=8):
    #Hash the url with the time entropy for randomness for same url 
    full_hash_rand=hashlib.sha256(f"{url}{datetime.now()}".encode()).hexdigest()
    length=random.randint(min_length,max_length)
    short_hash=full_hash_rand[:length+1]
    res= await check_code_exists(session,short_hash)
    if res:
        raise HTTPException(status_code=500,detail="Coudn''t generate unique short code,retry later or add custom code")
    return short_hash


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

        if have_slug:
            # user asked for that slug → conflict
            raise HTTPException(
                status_code=409,
                detail="Custom slug already exists; please choose another."
            )
        else:
            # extremely rare hash‑collision  
            # you can either let the client retry (they’ll get a fresh hash)…
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error, Retry. "
            )
    except Exception :
        # log and re-raise, map to 500 at a top-level handler
        await session.rollback()
        raise 
    

async def increment_stats(short_code: str) -> None:
    async with async_session() as session:  
        stmt = (
            update(URL_SHORTENER)
            .where(URL_SHORTENER.short_code == short_code,
                   URL_SHORTENER.deleted_at.is_(None))
            .values(
                visit_cnt       = URL_SHORTENER.visit_cnt + 1,
                last_accessed_at= datetime.now()
            )
        )
        await session.execute(stmt)
        await session.commit()


async def update_code_db(session,background_tasks,code,expiry_date,password):
    
    stmt=(
    update(URL_SHORTENER)
    .where(URL_SHORTENER.short_code==code,
           URL_SHORTENER.deleted_at.is_(None))
    .values(expiry_date=expiry_date,
            password=password)
    .returning(URL_SHORTENER.short_code,URL_SHORTENER.original_url,URL_SHORTENER.expiry_date,URL_SHORTENER.password,URL_SHORTENER.updated_at)
    )  #* make it to return only updated_at and original_url not now later after trying benchmarking
    result=await session.execute(stmt)
    res=result.first() 
    await session.commit()
    if not res:
        raise HTTPException(status_code=500,detail="Couldn't update code")
    
    #invalidate cache (or overwrite cache entry )
    await update_short_code_cache(code,res,background_tasks)
    
    return res

        
async def get_urls(session,user_id,limit,page):
    stmt=select(URL_SHORTENER).where(URL_SHORTENER.user_id==user_id,
        URL_SHORTENER.deleted_at.is_(None)
        ).offset((page-1)*limit).limit(limit)
    res=await session.execute(stmt)
    return res.scalars().all()

async def recent_urls(session,limit,offset):
    stmt = (
        select(
            URL_SHORTENER.id,
            URL_SHORTENER.original_url,
            URL_SHORTENER.short_code,
            URL_SHORTENER.created_at,
            URL_SHORTENER.visit_cnt,
        )
        .where(URL_SHORTENER.deleted_at.is_(None))              
        .order_by(desc(URL_SHORTENER.created_at))             
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(stmt)
    rows = result.all()  # List[Row] tuples with named attributes

    return [
        {
            "id":           row.id,
            "original_url": row.original_url,
            "short_code":   row.short_code,
            "created_at":   row.created_at,
            "visit_cnt":    row.visit_cnt,
        }
        for row in rows
    ]

async def del_scode(session,short_code):
    """Soft delete a short code by setting deleted_at timestamp"""
    result = await session.execute(
        update(URL_SHORTENER)
        .where(URL_SHORTENER.short_code == short_code,
               URL_SHORTENER.deleted_at.is_(None))
        .values(deleted_at=func.now())
    )

    # Check if any rows were updated
    if result.rowcount == 0: 
        raise HTTPException(status_code=404, detail="Short code not found or already deleted")
    await session.commit()
    