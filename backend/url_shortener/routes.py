import asyncio
from typing import List, Optional, Union
from fastapi import APIRouter, Header
from fastapi import Request, Depends, HTTPException
from fastapi.params import Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import  AsyncSession
from backend.common.utils import check_is_date_valid
from backend.url_shortener.dependencies import validate_payload
from db.schema import URL_SHORTENER
from .repository import del_scode, get_userid_scode, load_url
from db.dependencies import get_session, get_session_factory
from .models import  DateValidator, LongUrl
from.services import process_url
from datetime import date, datetime

urls_router=APIRouter()


@urls_router.post("/shorten")
async def shorten_url(request:Request,payload:LongUrl=Depends(validate_payload),db_session=Depends(get_session)):
    user_identifier = request.state.user_identifier
   
    res=await process_url(payload,db_session,user_identifier.id) 
    return res


@urls_router.post("/shorten/batch")
async def shorten_url(request:Request,payload:List[LongUrl],session_factory=Depends(get_session_factory)): 

    user_identifier = request.state.user_identifier

    print("Enterprise tier user")
    #sequential approach
    # try:
    #     results=[await process_url(payload_item,session,user_identifier) for payload_item in payload]
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")
    # print(results)

    #parallel approach (for small batch sizes no clear performance difference)
    async def _process_single(item:LongUrl):
        async with session_factory() as session:
            return await process_url(item, session, user_identifier)
 
    try:
        results=await asyncio.gather(*[_process_single(item) for item in payload])
        print(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

    successes=[result for result in results if result.get("error", None) is None]
    failures=[result for result in results if result.get("error", None) is not None]

    return {"successes": successes, "failures": failures}  


@urls_router.get("/redirect")
async def redirect_url(short_code:str,password:Optional[str]=None,db_session:AsyncSession=Depends(get_session)):
    
    url=await load_url(short_code,db_session)
   
    if url is None:
       raise HTTPException(status_code=404, detail="URL not found")
    
    if url.password and url.password!=password:
        raise HTTPException(status_code=401,detail="Invalid password as short code is protected")
    
    if url.expiry_date and url.expiry_date< datetime.now().date():
       raise HTTPException(status_code=410,detail="Code already expired")
    
    # stmt=(
    #     update(URL_SHORTENER)
    #     .where(URL_SHORTENER.short_code == short_code)
    #     .values(
    #         last_accessed_at=datetime.now(),
    #         visit_cnt=(URL_SHORTENER.visit_cnt + 1)
    #     )
    #     .returning(URL_SHORTENER.original_url,URL_SHORTENER.expiry_date,URL_SHORTENER.password)
    # )
    # await db_session.execute(stmt)
    
    
    url.last_accessed_at=datetime.now()
    url.visit_cnt += 1


    await db_session.commit()

    print("url",url)
    return RedirectResponse(url=url.original_url,status_code=307)


@urls_router.patch("/shorten/{short_code}")
async def update_code(
    request:Request,
    short_code:str,expiry_date:Optional[datetime]=None,password:Optional[str]=None,
    db_session:AsyncSession=Depends(get_session)):

    user_identifier = request.state.user_identifier

    user_id=user_identifier.id if user_identifier else None

    if not user_id:
        raise HTTPException(status_code=403,detail="Not a valid api key")

    code_exists=await get_userid_scode(short_code,db_session)
    if not code_exists:
        raise HTTPException(status_code=404, detail="Short code not found")
    
    if code_exists.user_id!=user_id:
        raise HTTPException(status_code=403,detail="Cannot update ,code belongs to another user")
    
    if code_exists.deleted_at is not None:
        raise HTTPException(status_code=410,detail="Code already deleted")
    valid_date=check_is_date_valid(expiry_date)
 
    if valid_date:
        stmt=(
        update(URL_SHORTENER)
        .where(URL_SHORTENER.short_code==short_code)
        .values(expiry_date=expiry_date,
                password=password)
        .returning(URL_SHORTENER.short_code,URL_SHORTENER.expiry_date)
        )
        result=await db_session.execute(stmt)
        await db_session.commit()
        res=result.first() if result else None
    
    return {"short_code":res.short_code,"expiry_date":res.expiry_date,"password":password,"message":"updated short code!"}


@urls_router.get("/urls")
async def get_all_urls_for_user(request:Request,db_session:AsyncSession=Depends(get_session),page:int=1,limit:int=10):
    user_identifier = request.state.user_identifier
    user_id=user_identifier.id if user_identifier else None

    if not user_id:
        raise HTTPException(status_code=403,detail="Not a valid api key")
    
    
    stmt=select(URL_SHORTENER).where(URL_SHORTENER.user_id==user_id).limit(limit).offset((page-1)*limit)
    all_urls_res=await db_session.execute(stmt)
    # all_urls=all_urls_res.scalars().all()  # response already in required dict format 
    all_urls=all_urls_res.scalars()   # for selecting all rows while using .scalars only it needs to serialised to proper format, fetchall gives objects list so define __repr__ method to change the result in required format
    return {"user_id":user_id,"urls":[row.to_dict() for row in all_urls],"page":page,"urls_count":limit}
    # return all_urls    
    

@urls_router.delete("/shorten/{short_code}")
async def remove_scode(request:Request,short_code:str,db_session:AsyncSession=Depends(get_session)):

    user_identifier = request.state.user_identifier
    user_id=user_identifier.id if user_identifier else None
    scode_user_id=await get_userid_scode(short_code,db_session)

    print("user_id",user_id)
    print("scodeid",scode_user_id)
    
    if scode_user_id :  # will be None in case of no short_code 
        if user_id :
            if scode_user_id.user_id==user_id:
                if not scode_user_id.deleted_at:  
                    await del_scode(db_session,short_code)
                    return f"{short_code} short code has been deleted"
                raise HTTPException(status_code=410,detail="Code already deleted")
            elif scode_user_id.user_id is None:  # to allow for deletions for case where no user associated with earlier codes
                return f"{short_code} short code has been deleted" 
            raise HTTPException(status_code=403,detail="Cannot delete,Code does not belong to user")
        else:
           raise HTTPException(status_code=403,detail="Not a valid api key")
    else:
        raise HTTPException(status_code=404,detail='Not a valid short code')