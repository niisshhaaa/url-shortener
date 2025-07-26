import asyncio
from typing import List, Optional, Union
from fastapi import APIRouter, Header
from fastapi import Request, Depends, HTTPException,BackgroundTasks
from fastapi.params import Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import  AsyncSession
from backend.url_shortener.dependencies import validate_batch_payload, validate_payload
from .repository import  del_scode, get_urls, get_userid_scode, increment_stats, load_url, recent_urls, update_code_db
from db.dependencies import get_session, get_session_factory
from .models import  LongUrl, ShortenResponse, UpdateShortUrl
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

    valids_with_idx, failures = payload

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
        results=await asyncio.gather(*[_process_single(idx,item) for idx,item in valids_with_idx])
        print(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")

    successes=[result for result in results if "result" in result]
    failures=failures or [result for result in results if "error" in result] 

    return {"successes": successes, "failures": failures}  


@urls_router.get("/redirect")
async def redirect_url(short_code:str,background_tasks:BackgroundTasks,
                    password:Optional[str]=Query(None),
                    db_session:AsyncSession=Depends(get_session)):
    
    url=await load_url(short_code,db_session)

    print("url",url)
   
    if url is None:
       raise HTTPException(status_code=404, detail="Code not found or deleted")
    
    if url.password and url.password!=password:  #passwords should certainly be hashed in auth scenarios  
        raise HTTPException(status_code=403,detail="Invalid password as short code is protected")
    
    if url.expiry_date and url.expiry_date< datetime.now().date():
       raise HTTPException(status_code=410,detail="Code already expired")


    #  Kick off analytics increment after sending redirect in same thread
    background_tasks.add_task(increment_stats, short_code)
    
    return RedirectResponse(url=url.original_url,status_code=307)


@urls_router.patch("/shorten/{short_code}")
async def update_code(
    request:Request,
    short_code:str,
    patch_payload:UpdateShortUrl,
    db_session:AsyncSession=Depends(get_session)):

    user_identifier = request.state.user_identifier
    user_id=user_identifier.id 


    code=await get_userid_scode(short_code,db_session)
    if not code:
        raise HTTPException(status_code=404, detail="Short code not found or deleted")
    
    if code.user_id!=user_id:
        raise HTTPException(status_code=403,detail="Cannot update ,code belongs to another user")
    
    if code.password and code.password!=patch_payload.password:    
        raise HTTPException(status_code=403,detail="Invalid password as short code is protected")
    
    res=await update_code_db(db_session,code.short_code,patch_payload.expiry_date,patch_payload.new_password)
    return {"short_code":res.short_code,"expiry_date":res.expiry_date,"password":res.password,"message":"updated short code!"}


@urls_router.get("/urls")
async def get_all_urls_for_user(
    request:Request,db_session:AsyncSession=Depends(get_session),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    ):
    user_identifier = request.state.user_identifier
    user_id=user_identifier.id 

    urls=await get_urls(db_session,user_id,limit,page)

    if not urls:
        raise HTTPException(status_code=403,detail="Invalid auth or urls not found")
    return urls   



@urls_router.get("/latest-urls")
async def latest_urls(
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    db_session: AsyncSession = Depends(get_session),
):
    records=await recent_urls(db_session,limit,offset=(page-1)*limit)
    print("records",records)
    if not records:
        raise HTTPException(404, detail="No URLs found")
    return records

#Add password check in this as well
@urls_router.delete("/shorten/{short_code}")
async def remove_scode(short_code:str,db_session:AsyncSession=Depends(get_session)):
   
    await del_scode(db_session,short_code)
    return {"message": f"{short_code} short code has been deleted"}
    
    

@urls_router.get("/health")
async def health_check(db_session:AsyncSession=Depends(get_session)):
    try:
        stmt=text("SELECT 1")  
        await db_session.execute(stmt)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

 




    

