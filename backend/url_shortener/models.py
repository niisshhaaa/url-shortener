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

class DateValidator(BaseModel):
    exp_date: Optional[date] = Field(
        None,
        description="New expiration date in YYYY-MM-DD (must be future)",
        example="2025-08-15",
    )

    @field_validator("exp_date")
    def must_be_future(cls, v: Optional[date]) -> Optional[date]:
        if v and v <= date.today():
            raise ValueError("expiry_date must be strictly in the future")
        return v