from fastapi import FastAPI,Header,HTTPException,Depends,APIRouter, Request
from datetime import datetime
from typing import Union,Optional,List
from sqlalchemy import select,delete,func,update
from fastapi.responses import RedirectResponse
from dotenv import find_dotenv, load_dotenv
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.db_utils import get_idntier_api_key
from backend.services import check_api_key, get_id_api_key,get_userid_scode, load_url, process_url, url_to_update,del_scode
from db.schema import URL_SHORTENER,Users
import asyncio
from .utils import check_is_date_valid
from .dependencies import AccessTokenBearer,RefreshTokenBearer,get_session,get_session_factory
from middlewares.middlewares import RequestLoggingMiddleware
from .models import LongUrl,BatchUrls,UserCreateModel,LoginInput,Token

load_dotenv(find_dotenv(raise_error_if_not_found=True), override=True)

urls_router=APIRouter()

accessTokenBearer=AccessTokenBearer()
refreshTokenBearer=RefreshTokenBearer()



@urls_router.post("/shorten")
async def shorten_url(payload:LongUrl,api_key:str=Header(...),db_session=Depends(get_session)):
    get_user_id_reqst=await check_api_key(api_key,db_session)
   
    res=await process_url(payload,db_session,get_user_id_reqst) 
    return res
 
# for batch endpoint if separate from single post endpoint don't allow single url payload,
# here it is just for example if a single endpoint were to handle both single url and batch url payload.
@urls_router.post("/shorten/batch")
async def shorten_url(payload:Union[LongUrl,List[LongUrl]],api_key:str=Header(...),db_session=Depends(get_session_factory)): 
    async with db_session() as session:
        get_user_id_reqst=await check_api_key(api_key,session)
   
    if isinstance(payload,LongUrl):
        async with db_session() as session:
            resp=await process_url(payload,session,get_user_id_reqst) 
            if resp["error"]:
                raise resp["error"]  
            return resp
            
    elif isinstance(payload,list) and get_user_id_reqst.tier_level=='ENTERPRISE':
        async with db_session() as session:
            results=await asyncio.gather(*[process_url(payload_item,session,get_user_id_reqst) for payload_item in payload])

        successes=[result for result in results if result["error"] is None]
        failures=[result for result in results if result["error"] is not None]

        return {"successes": successes, "failures": failures}
    elif isinstance(payload,list) and get_user_id_reqst.tier_level=='HOBBY':
        raise HTTPException(status_code=400, detail="Invalid request for Hobby tier without pricing")
    else:
        raise HTTPException(status_code=422, detail="Unprocessable entity,invalid input format")
    

@urls_router.get("/redirect")
async def redirect_url(short_code:str,user_id=Depends(check_api_key),password:Optional[str]=None,db_session:AsyncSession=Depends(get_session)):
    
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
    short_code:str,expiry_date:Optional[datetime],password:Optional[str]=None,api_key:str=Header(...),
    db_session:AsyncSession=Depends(get_session)):
    get_user=await get_idntier_api_key(api_key,db_session)
    get_user_id=get_user.id if get_user else None  

    if not get_user_id:
        raise HTTPException(status_code=403,detail="Not a valid api key")

    code_exists=await get_userid_scode(short_code,db_session)
    if not code_exists:
        raise HTTPException(status_code=404, detail="Short code not found")
    
    if code_exists.user_id!=get_user_id:
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


@urls_router.get("/user/urls")
async def get_all_urls_for_user(api_key:str=Header(...),db_session:AsyncSession=Depends(get_session),page:int=1,limit:int=10):
    get_user=await get_idntier_api_key(api_key,db_session)
    get_user_id=get_user.id if get_user else None


    if not get_user_id:
        raise HTTPException(status_code=403,detail="Not a valid api key")
    
    
    stmt=select(URL_SHORTENER).where(URL_SHORTENER.user_id==get_user_id).limit(limit).offset((page-1)*limit)
    all_urls_res=await db_session.execute(stmt)
    # all_urls=all_urls_res.scalars().all()  # response already in required dict format 
    all_urls=all_urls_res.scalars()   # for selecting all rows while using .scalars only it needs to serialised to proper format, fetchall gives objects list so define __repr__ method to change the result in required format
    return {"user_id":get_user_id,"urls":[row.to_dict() for row in all_urls],"page":page,"urls_count":limit}
    # return all_urls    
    

@urls_router.delete("/shorten/{short_code}")
async def remove_scode(short_code:str,api_key:str=Header(...),db_session:AsyncSession=Depends(get_session)):

    api_key_id=await get_id_api_key(api_key,db_session)
    scode_user_id=await get_userid_scode(short_code,db_session)

    print("api_key_id",api_key_id)
    print("scodeid",scode_user_id)
    
    if scode_user_id :  # will be None in case of no short_code 
        if api_key_id :
            if scode_user_id.user_id==api_key_id.id:
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
        
            

async def get_real_time_analytics(session,limit,offset):
    result=await session.execute(
           select(URL_SHORTENER).order_by(URL_SHORTENER.created_at.desc()).limit(limit)
        )
    # statement2=select(func.count(URL_SHORTENER.short_code).label("total_urls"))
    # result2=await session.execute(statement2)
    # print(result2.fetchone()) #(10001057,)
    scalars=result.scalars()
    result=scalars.all()
    print("scalars result" , scalars) # <sqlalchemy.engine.result.ScalarResult object at 0x000001CDAE829680>
    print("result all",result) #[<db.schema.URL_SHORTENER object at 0x000001CDAEE30C10>, <db.schema.URL_SHORTENER object at 0x000001CDAEA072D0>, ...
    return result


# @app.get("/analytics/real-time")
# async def real_time_analytics(db_session:AsyncSession=Depends(get_session), limit:int=10, offset:int=0):
#     data = await get_real_time_analytics(db_session,limit,offset)
#     if not data:
#         raise HTTPException(status_code=404, detail="Error in getting real time analytics")
#     # return [row.to_dict() for row in data]
#     return data













# Handling of race conditions --
#A race condition occurs when two or more processes or threads attempt to perform an operation on shared resources simultaneously in such a way 
# that the outcome depends on the timing or order of execution.
# 1) Same payload at same time ( more than 1 user requests short code for same url at same time)
# one requests succeeds , other requests will cause integrity error as short code should be unique
# 2) Different payload with same hash codes which don't already exist, added the integrity error checks to handle that .


    
    





