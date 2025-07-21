import asyncio
from typing import List, Optional, Union
from fastapi import APIRouter, Header
from fastapi import Request, Depends, HTTPException,BackgroundTasks
from fastapi.params import Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import  AsyncSession
from backend.url_shortener.dependencies import validate_batch_payload, validate_payload
from .repository import  get_urls, get_userid_scode, increment_stats, load_url, recent_urls, update_code_db
from db.dependencies import get_session, get_session_factory
from .models import  LongUrl, ShortenResponse
from.services import process_url
from datetime import date, datetime

urls_router=APIRouter()


@urls_router.post("/shorten",response_model=ShortenResponse)
async def shorten_url(request:Request,payload:LongUrl=Depends(validate_payload),db_session=Depends(get_session)):
    user_identifier = request.state.user_identifier

    res=await process_url(payload,db_session,user_identifier.id) 
    return res


@urls_router.post("/shorten/batch")
async def shorten_url(request:Request,payload:List[LongUrl]=Depends(validate_batch_payload),session_factory=Depends(get_session_factory)): 

    user_identifier = request.state.user_identifier

    #sequential approach
    # try:
    #     results=[await process_url(payload_item,session,user_identifier) for payload_item in payload]
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")
    # print(results)

    #parallel approach (for small batch sizes no clear performance difference)
    async def _process_single(idx:int,item:LongUrl):
        async with session_factory() as session:
                try:
                    res=await process_url(item, session, user_identifier.id)
                    return {"index": idx, "result": res}
                except Exception as e:
                    return {"index": idx, "error": str(e)}

 
    try:
        results=await asyncio.gather(*[_process_single(idx,item) for idx,item in enumerate(payload)])
        print(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

    successes=[result for result in results if "result" in result]
    failures=[result for result in results if "error" in result]

    return {"successes": successes, "failures": failures}  


@urls_router.get("/redirect")
async def redirect_url(short_code:str,background_tasks:BackgroundTasks,password:Optional[str]=None,db_session:AsyncSession=Depends(get_session)):
    
    
    url=await load_url(short_code,db_session)
   
    if url is None:
       raise HTTPException(status_code=404, detail="URL not found")
    
    if url.password and password and url.password!=password:
        raise HTTPException(status_code=401,detail="Invalid password as short code is protected")
    
    if url.expiry_date and url.expiry_date< datetime.now().date():
       raise HTTPException(status_code=410,detail="Code already expired")
    

    #  Kick off analytics increment after sending redirect in same thread
    background_tasks.add_task(increment_stats, short_code)
    
    return RedirectResponse(url=url.original_url,status_code=307)


@urls_router.patch("/shorten/{short_code}")
async def update_code(
    request:Request,
    short_code:str,
    expiry_date: Optional[date] = Query(
        None,
        description="New expiration date in YYYY-MM-DD ",
        example="2025-08-15",
    ),
    password:Optional[str]=None,
    db_session:AsyncSession=Depends(get_session)):

    user_identifier = request.state.user_identifier
    user_id=user_identifier.id 

    if not expiry_date and not password:
        return {"message":"Please provide fields to update"}

    code=await get_userid_scode(short_code,db_session)
    if not code:
        raise HTTPException(status_code=404, detail="Short code not found")
    
    if code.user_id!=user_id:
        raise HTTPException(status_code=403,detail="Cannot update ,code belongs to another user")
    
    if code.deleted_at:
        raise HTTPException(status_code=410,detail="Code already deleted")
    
    res=await update_code_db(db_session,code.short_code,expiry_date,password)
    return {"short_code":res.short_code,"expiry_date":res.expiry_date,"password":password,"message":"updated short code!"}


@urls_router.get("/urls")
async def get_all_urls_for_user(
    request:Request,db_session:AsyncSession=Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=20),
    ):
    user_identifier = request.state.user_identifier
    user_id=user_identifier.id 

    urls=await get_urls(db_session,user_id,limit,page)

    if not urls:
        return {"message":"No urls found"}
    return urls   



@urls_router.get("/latest-urls")
async def latest_urls(
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    db_session: AsyncSession = Depends(get_session),
):
    records=await recent_urls(db_session,limit,offset=(page-1)*limit)
    if not records:
        raise HTTPException(404, detail="No URLs found")
    return records


@urls_router.get("/health")
async def health_check(db_session:AsyncSession=Depends(get_session)):
    try:
        stmt=text("SELECT 1")  
        await db_session.execute(stmt)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

 




    

