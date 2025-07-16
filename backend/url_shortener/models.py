from datetime import datetime
from typing import List, Union
from pydantic import BaseModel


class LongUrl(BaseModel):
    url_link:str
    custom_slug:Union[str, None] = None
    exp_date:Union[datetime,None]= None
    password:Union[str,None]=None


