from fastapi import FastAPI,Header,status,Request
from pydantic import BaseModel
from fastapi import HTTPException,Depends
import hashlib
from datetime import datetime
from typing import Union,Optional,List,AsyncGenerator
from sqlalchemy import select,delete,func,update
from sqlalchemy.exc import IntegrityError
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import  AsyncSession
from sqlalchemy.orm import sessionmaker
from db.schema import URL_SHORTENER,Users,TierLevel
from urllib.parse import urlparse
import socket
import string,random,asyncio
from .utils import gen_password_hash,generate_api_key,verify_pass,create_token,decode_token
from .dependencies import TokenBearer,AccessTokenBearer,RefreshTokenBearer,get_session,get_session_factory,app
from .middlewares import RequestTimingMiddleware,AuthenticationMiddleware

load_dotenv()

app.add_middleware(RequestTimingMiddleware)
class LongUrl(BaseModel):
    url_link:str
    custom_slug:Union[str, None] = None
    exp_date:Union[str,None]= None
    password:Union[str,None]=None

class BatchUrls(BaseModel):
    batch:List[LongUrl]

class UserCreateModel(BaseModel):
    username:Union[str,None]=None
    email:str
    password:str

class LoginInput(BaseModel):
    email:str
    password:str

class Token(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str="bearer"

accessTokenBearer=AccessTokenBearer()
refreshTokenBearer=RefreshTokenBearer()


async def check_code_exists(session,short_code:str):
    print('entered',short_code)
    result = await session.execute(
       select(URL_SHORTENER.original_url,URL_SHORTENER.short_code).where(URL_SHORTENER.short_code==short_code)
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

async def save_url(session,userid,original_url:str,short_code:str,exp_date:Optional[datetime]=None,password:Optional[str]=None):  
   
    new_url=URL_SHORTENER(original_url=original_url,short_code=short_code,user_id=userid,expiry_date=exp_date,password=password)
    session.add(new_url)
    try:
        await session.commit()
        await session.refresh(new_url)
        return new_url
    except IntegrityError:
        await session.rollback()
        # return new_url   #can return directly without below checks if there was no hash collision issue with  different users different payloads , hash code not already existing in db 
        code_exists=await check_code_exists(session,short_code)
        code_exists_url=code_exists.original_url if code_exists else None
        code_exists_scode=code_exists.short_code if code_exists else None
        if code_exists_scode:
            if code_exists_url==original_url:
               return new_url
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

    


# def shorten_url(payload:LongUrl,db_conn=Depends(get_db_connection)):  
#     short_code=payload.custom_slug
#     if short_code:
#         if check_code_exists(db_conn,short_code):
#             raise HTTPException(status_code=500,detail='Please enter a unique code ,it already exists')
    
#     else:
#         hash_code=hashlib.md5(payload.url_link.encode()).hexdigest()[:6]
#         print("hash-code",hash_code)
#         short_code=retry_ifnot_unq(hash_code,payload,db_conn)
    
#     newinsert= save_url(db_conn,original_url=payload.url_link,short_code=short_code)
#     print('newinsert',newinsert)
#     response={"short_url":f"{DOMAIN}{newinsert[2]}"}
#     return response

def is_valid_url(url: str):
    """
    Validate the URL format and check if it's secure and resolved to a valid domain.
    """
    parsed = urlparse(url)
    # "scheme://netloc/path;parameters?query#fragment"

    try:
        # Check for valid scheme and netloc
        if parsed.scheme not in ["http", "https"] or not bool(parsed.netloc):
            return False
        hostname = parsed.netloc.split(":")[0]

        #check if hostname resolves to an ip address (i.e. domain exists)
        hostip=socket.gethostbyname(hostname)

        return hostip and True
    
    except (ValueError,socket.gaierror) :
        return False
    
def random_code(min_length=5,max_length=8):
    #Hash the url with the time entropy for randomness for same url 
    chars=string.ascii_letters + string.digits
    return "".join(random.choices(chars,k=2))


def hash_code_with_entropy(url,min_length=5,max_length=8):
    #Hash the url with the time entropy for randomness for same url 
    full_hash_rand=hashlib.sha256(f"{url}{datetime.now()}".encode()).hexdigest()
    length=random.randint(min_length,max_length)
    short_hash=full_hash_rand[:length+1]
    return short_hash


async def retry_ifnot_unq(short_code:str,url,session):
    
    max_attempts = 5
    attempts = 0
    while True:
        hash_code_new = hash_code_with_entropy(url)+random_code()
        code_exists=await check_code_exists(session,hash_code_new) 
        code_exists_scode=code_exists.URL_SHORTENER.short_code if code_exists else None 
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

def check_is_date_valid(date):
        try:
            date=date
            # print(date.date(),date.now().date(),datetime.now().date())
            if isinstance(date,str):       # date from payload
                date=datetime.fromisoformat(date)
            
            if isinstance(date,datetime):  # from query parameter of update request
                date=date.date()
            
            if date>=datetime.now().date():
                return date
            else:
                raise HTTPException(status_code=400,detail="Dates before today not allowed")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expiry date format. Use YYYY-MM-DD ")

    


# async def shorten_url(payload:LongUrl,api_key:str=Header(...),db_session:AsyncSession=Depends(get_session)): 
#     if not is_valid_url(payload.url_link):
#         raise HTTPException(
#             status_code=400, detail="Invalid or insecure URL format")
    
#     valid_date=None
#     if payload.exp_date:
#         valid_date=check_is_date_valid(payload.exp_date)
    
#     get_user_id_reqst=await get_idntier_api_key(api_key,db_session)
#     if not get_user_id_reqst:
#         raise HTTPException(status_code=403,detail="Not a valid api key")
    
#     user_id_reqst=get_user_id_reqst.id

#     if payload.custom_slug:
#         slug_code=payload.custom_slug
#         code_exists=await check_code_exists(db_session,slug_code)
#         if code_exists:
#             raise HTTPException(status_code=409,detail="Code already exits, Retry")
#         short_code=slug_code
#         newinsert=await save_url(db_session,user_id_reqst,original_url=payload.url_link,short_code=short_code,exp_date=valid_date)
#         print('newinsert',newinsert)
#         response={"short_url":f"{newinsert.short_code}"}
#     else:
#         hash_code=hash_code_with_entropy(payload.url_link)
#         code_exists=await check_code_exists(db_session,hash_code)
#         code_exists_scode=code_exists.short_code if code_exists else None
#         if code_exists_scode:
#             short_code=await retry_ifnot_unq(hash_code,payload.url_link,db_session)
#             newinsert= await save_url(db_session,user_id_reqst,original_url=payload.url_link,short_code=short_code,exp_date=valid_date)
#             print('newinsert',newinsert)
#             response={"short_url":f"{newinsert.short_code}"}
            
#         else:
#             short_code=hash_code
#             newinsert=await save_url(db_session,user_id_reqst,original_url=payload.url_link,short_code=short_code,exp_date=valid_date)
#             print('newinsert',newinsert)
#             response={"short_url":f"{newinsert.short_code}"}

#     return response

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
                        raise HTTPException(status_code=409,detail="Code already exits, Retry")
                    short_code=slug_code
                    newinsert=await save_url(session,user_id_reqst,original_url=payload.url_link,
                                             short_code=short_code,exp_date=valid_date,password=payload.password)
                    print('newinsert',newinsert)
                    response={"original_url":newinsert.original_url,"short_url":newinsert.short_code,"pass":newinsert.password,"error":None}
                else:
                    hash_code=hash_code_with_entropy(payload.url_link)
                    code_exists=await check_code_exists(session,hash_code)
                    code_exists_scode=code_exists.short_code if code_exists else None
                    if code_exists_scode:
                        short_code=await retry_ifnot_unq(hash_code,payload.url_link,session)
                        newinsert= await save_url(session,user_id_reqst,original_url=payload.url_link,
                                                  short_code=short_code,exp_date=valid_date,password=payload.password)
                        print('newinsert',newinsert)
                        response={"original_url":newinsert.original_url,"short_url":newinsert.short_code,"pass":newinsert.password,"error":None}
                        
                    else:
                        short_code=hash_code
                        newinsert=await save_url(session,user_id_reqst,original_url=payload.url_link,
                                                 short_code=short_code,exp_date=valid_date,password=payload.password)
                        print('newinsert',newinsert)
                        response={"original_url":newinsert.original_url,"short_url":newinsert.short_code,"pass":newinsert.password,"error":None}
                
                return response

            except Exception as e:
                 return {"url":payload.url_link,"short_code":None,"error":e}
            # to catch the raised error for a particular url processing

async def check_api_key(api_key,sessionfactory):
    async with sessionfactory() as session:
        get_user_id_reqst=await get_idntier_api_key(api_key,session)
        get_user_id_reqst_id=get_user_id_reqst.id if get_user_id_reqst else None
        if not get_user_id_reqst_id:
            raise HTTPException(status_code=403,detail="Not a valid api key")
        return get_user_id_reqst
    


@app.post("/shorten")
async def shorten_url(payload:Union[LongUrl,List[LongUrl]],api_key:str=Header(...),db_session=Depends(get_session_factory)): 
    get_user_id_reqst=await check_api_key(api_key,db_session)
   
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
    
# @app.post("/shorten/batch")
# async def shorten_urls(payload:List[LongUrl],api_key:str=Header(...),db_session:sessionmaker=Depends(get_session_factory)):
#     pass


@app.get("/redirect")
async def redirect_url(short_code:str,password:Optional[str]=None,db_session:AsyncSession=Depends(get_session)):
    stmt=(
        update(URL_SHORTENER)
        .where(URL_SHORTENER.short_code == short_code)
        .values(
            last_accessed_at=datetime.now(),
            visit_cnt=(URL_SHORTENER.visit_cnt + 1)
        )
        .returning(URL_SHORTENER.original_url,URL_SHORTENER.expiry_date,URL_SHORTENER.password)
    )

    result=await db_session.execute(stmt)
    url=result.first() if result else None

    if url is None:
       raise HTTPException(status_code=404, detail="URL not found")
    
    if url.password and url.password!=password:
        raise HTTPException(status_code=401,detail="Invalid password as short code is protected")
    
    if url.expiry_date and url.expiry_date< datetime.now().date():
       raise HTTPException(status_code=410,detail="Code already expired")
    
    
    await db_session.commit()
    print("url",url)
    return RedirectResponse(url=url.original_url,status_code=307)
    # response = {"original_url": url}
    # return response

@app.patch("/shorten/{short_code}")
async def update_code(
    short_code:str,expiry_date:Optional[datetime],password:Optional[str]=None,api_key:str=Header(...),
    db_session:AsyncSession=Depends(get_session)
    # ,jwtTokenBearer=Depends(accessTokenBearer)
    ):
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


@app.get("/user/urls")
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

# @app.get("/user/urls")
# async def get_all_urls_for_user(request:Request,db_session:AsyncSession=Depends(get_session),page:int=1,limit:int=10):
#     get_user=getattr(request.state,"idntier",None)
#     get_user_id=get_user.id if get_user else None


#     if not get_user_id:
#         raise HTTPException(status_code=403,detail="Not a valid api key")
    
    
#     stmt=select(URL_SHORTENER).where(URL_SHORTENER.user_id==get_user_id).limit(limit).offset((page-1)*limit)
#     all_urls_res=await db_session.execute(stmt)
#     # all_urls=all_urls_res.scalars().all()  # response already in required dict format 
#     all_urls=all_urls_res.scalars()   # for selecting all rows while using .scalars only it needs to serialised to proper format, fetchall gives objects list so define __repr__ method to change the result in required format
#     return {"user_id":get_user_id,"urls":[row.to_dict() for row in all_urls],"page":page,"urls_count":limit}
    
    

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


@app.delete("/shorten/{short_code}")
async def remove_scode(short_code:str,api_key:str=Header(...),db_session:AsyncSession=Depends(get_session),
                    #    jwtTokenBearer=Depends(accessTokenBearer)
                       ):
    """
    A user cannot delete other user's codes but can delete codes where no user associated with them (for already existing rows)
    """
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


"""User Routes ---->"""
# # async def user_exists(email,session):
# #     user=await get_user(email,session)
# #     return True if user else False

# async def get_user(email:str,session):
#     stmt=select(Users.id,Users.email,Users.api_key,Users.created_at,Users.password_hash,Users.tier_level).where(Users.email==email)
#     result=await session.execute(stmt)
#     return result.first()


# # async def user_exists_get_key(email,session):
# #     user=await get_user(email,session)

# #     if user.email and user.api_key:
# #         if not user.password_hash:
# #             apiKey=user.api_key
# #             return user.api_key
# #         return None
    
# #     apiKey=None
# #     return (apiKey,)

# async def user_exists_get_key(email,session):
#     """also include user.api_key for checking to be consistent with old schema
#        api key won't be deleted to ensure backward compatibility for this project
#     """
#     user=await get_user(email,session)
#     print("user",user)
#     print("getkey",user.email)
#     print('passhash',user.password_hash)
#     print("tierle",user.tier_level)
     
#     if user.email and user.api_key:
#         """the below condition will be removed after existing accounts update/add passwords"""
#         if not user.password_hash:
#             return user.api_key
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Account already exists with this email")
    
#     return None



# async def create_user(userData:UserCreateModel,session,apiKey):
#     pass_hash=gen_password_hash(userData.password)
    
#     new_user=Users(name=userData.username,email=userData.email,password_hash=pass_hash,api_key=apiKey)

#     try:
#         session.add(new_user)
#         await session.commit()
#         await session.refresh(new_user)
#         return new_user
#     except IntegrityError:
#         await session.rollback()
#         raise HTTPException(status_code=410,detail='User with this email already exists')
#     except Exception as e:
#         await session.rollback()
#         raise e
    

# async def add_password(userData:UserCreateModel,session):
#     pass_hash=gen_password_hash(userData.password)

#     try:
#         stmt=update(Users).where(Users.email==userData.email).values(password_hash=pass_hash).returning(Users.id,Users.email,Users.password_hash)
#         result=await session.execute(stmt)
#         await session.commit()
#         return result.first()
#     except IntegrityError:
#         await session.rollback()
#         raise HTTPException(status_code=410,detail='User with this email already exists')
#     except Exception as e:
#         await session.rollback()
#         raise e




# #we can deactivate the accounts of user who don't migrate to new authentication method within given time duration

# @app.post("/user/signup",status_code=status.HTTP_201_CREATED)
# async def create_user_account(userCreatePayload:UserCreateModel,db_session:AsyncSession=Depends(get_session)):
#     email=userCreatePayload.email
#     print("signupemail",email)
    
#     try:
#         userExistsKey=await user_exists_get_key(email,db_session)

#         if userExistsKey:
#             userWithPass=await add_password(userCreatePayload,db_session)
#             return {"message":"Account created successfully!"}
        
#         new_api_key = generate_api_key()
#         new_user = await create_user(userCreatePayload, db_session, new_api_key)
#         return {"message":"Account created successfully!"}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         await db_session.rollback()
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    


# @app.post("/user/login")
# async def login_user(loginPayload:LoginInput,db_session:AsyncSession=Depends(get_session)):
#     user=await get_user(loginPayload.email,db_session)

#     if not user :
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="No account exists for this email")
    
#     isPassValid=verify_pass(loginPayload.password,user.password_hash)
#     print(isPassValid)
#     if not isPassValid:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Password is incorrect")
    
#     access_token=create_token(userIdentity={'email':user.email,'user_id':user.id})
#     refresh_token=create_token(userIdentity={'email':user.email,'user_id':user.id},refresh=True)
#     return {"message":"Login successful","access_token":access_token,"refresh_token":refresh_token,"user":{'email':user.email,'user_id':user.id}}

# @app.get("/health",status_code=200)
# async def check_connection_health(db_session:AsyncSession=Depends(get_session)):
#     try:
#         await db_session.execute(select(URL_SHORTENER.id).where(URL_SHORTENER.id==1))
#         return {"status": "healthy","detailss":"server is running smoothly and database is connected"}
#     except Exception as e:
#         return {"status":"unhealthy","details":str(e)}
    
        
# @app.get("/refresh-token")
# async def refresh_newtoken(jwtToken:dict=Depends(refreshTokenBearer)):
#     expiry=jwtToken["exp"]
#     if datetime.fromtimestamp(expiry)>datetime.now():
#         new_token=create_token(jwtToken,refresh=True)
#         return {"new_token":new_token}
    
#     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,details="Expired Token")














# Handling of race conditions --
#A race condition occurs when two or more processes or threads attempt to perform an operation on shared resources simultaneously in such a way 
# that the outcome depends on the timing or order of execution.
# 1) Same payload at same time ( more than 1 user requests short code for same url at same time)
# one requests succeeds , other requests will cause integrity error as short code should be unique
# 2) Different payload with same hash codes which don't already exist, added the integrity error checks to handle that .


    
    





