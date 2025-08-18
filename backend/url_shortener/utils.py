import asyncio
import hashlib
import random
import socket
import string
import time
from urllib.parse import urlparse
from fastapi import HTTPException
from passlib.context import CryptContext
import secrets,os,jwt,uuid,logging
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime ,timedelta
from backend.cache._cache import redis_client
from backend.__init__ import logger
from backend.common.custom_exceptions import DBUnavailable
from sqlalchemy.exc import OperationalError


pass_context=CryptContext(schemes=['bcrypt'])


SECRET_KEY=os.getenv("SUPER_SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7



class TokenData(BaseModel):
    email:str

def gen_password_hash(password:str):
    hashp=pass_context.hash(password)
    return hashp

def verify_pass(passowrd:str,hash:str):
    return pass_context.verify(passowrd,hash)

def generate_api_key():
    return secrets.token_urlsafe(32)  # Generates a 43-character base64 string(A-Z,a-z,0-9)

def create_token(userIdentity:dict,expires_time:timedelta=None,refresh:bool=False):
    to_encode={}
    to_encode["userIdty"]=userIdentity
    if refresh:
        expiry=datetime.now() + (expires_time or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    else:
        expiry=datetime.now() + (expires_time if expires_time is not None else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"]=expiry
    to_encode["jti"]=str(uuid.uuid4())
    to_encode["refresh"]=refresh
    token= jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return token

# def create_refresh_token(userEmail:str):
#     expiry=datetime.now() + (timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
#     to_encode={"identity":userEmail,"expiry":expiry}
#     return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def decode_token(token:str):
    try:
        token_data=jwt.decode(
        jwt=token,
        key=SECRET_KEY,
        algorithms=ALGORITHM
        )
        return token_data
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None
    

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


def hash_code_without_entropy(url,user_id):
    full_hash_rand=hashlib.sha256(f"{url}{user_id}".encode()).hexdigest()
    short_hash=full_hash_rand[:7]
    return short_hash


async def general_retry(func, db_circuit,retry_exceptions, on_retry_log,retries=3, base_delay=0.1,max_delay=0.5):
    last_exc = None

    for i in range(retries):
       
        try:
            res = await func()
            await db_circuit.record_success()
            return res
        except OperationalError as e :
            while await db_circuit.allow_request():
                print("OperationalError occurred, retrying...")
                await db_circuit.record_failure()
                delay=min(max_delay, base_delay * (2 ** i)) 
                await asyncio.sleep(delay)
            raise e
        except retry_exceptions as e:
            last_exc = e
            delay=min(max_delay, base_delay * (2 ** i))
            if on_retry_log:
                on_retry_log(i,retries,delay,e)
            await asyncio.sleep(delay)

    raise last_exc

def on_retry_log(attempt,retries,delay, exc):
    logger.debug("Retry attempt %d/%d after %0.3fs due to %s", attempt, retries, delay, type(exc).__name__,str(exc))


async def make_attempt(session_factory,func, *args, **kwargs ):

    async def attempt():
        async with session_factory() as session:
            url=await func(session,*args, **kwargs)
            return url
        
    return attempt

