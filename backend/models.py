


from datetime import datetime
from typing import List, Union
from pydantic import BaseModel


class LongUrl(BaseModel):
    url_link:str
    custom_slug:Union[str, None] = None
    exp_date:Union[datetime,None]= None
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