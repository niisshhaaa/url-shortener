from datetime import datetime,date
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator ,HttpUrl


class LongUrl(BaseModel):
    url_link:HttpUrl  # Use HttpUrl type for URL validation
    custom_slug:Union[str, None] = None
    exp_date:Optional[date] = Field(
        None,
        description="New expiration date in YYYY-MM-DD (must be future)",
        example="2025-08-15",
    )
    password:Union[str,None]=None

class ShortenResponse(BaseModel):
    original_url: str
    short_url:    str
    password:     Optional[str]=None




class DateValidator(BaseModel):
    exp_date: Optional[date] = Field(
        None,
        description="New expiration date in YYYY-MM-DD (must be future)",
        example="2025-08-15",
    )

  