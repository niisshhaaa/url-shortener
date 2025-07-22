from datetime import date
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator ,HttpUrl


class LongUrl(BaseModel):
    url_link:HttpUrl  # Use HttpUrl type for URL validation
    custom_slug:Union[str, None] = Field(
        default=None,
        min_length=2,
        max_length=8,
        description="Optional custom slug (3-8 characters)"
    )
    exp_date:Optional[date] = Field(
        None,
        description="New expiration date in YYYY-MM-DD (must be future)",
        example="2025-08-15",
    )
    password:Union[str,None]=Field(
        default=None,
        min_length=6,
        max_length=15,
        description="Optional password (6-15 characters)"
    )

class ShortenResponse(BaseModel):
    original_url: str
    short_url:    str
    password:     Optional[str]=None


class UpdateShortUrl(BaseModel):
    expiry_date:     Optional[date] = Field(
        None,
        description="New expiration date in YYYY-MM-DD ",
        example="2025-08-15",
    )
    password: Optional[str] = Field(None,
    description="Must match existing password, if code is protected"
    )
    new_password:     Optional[str] = Field(
        None, min_length=6,
        description="New password to set (or null to remove password)"
    )



  