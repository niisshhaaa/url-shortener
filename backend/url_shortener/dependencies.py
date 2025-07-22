import re
import socket
import asyncio
from datetime import date
from functools import lru_cache
from typing import Any, List

from fastapi import Body, HTTPException
import pydantic
from sqlalchemy import Tuple


from backend.url_shortener.models import LongUrl

async def validate_date(exp_date):
        if exp_date is not None and exp_date < date.today():
            raise HTTPException(400, "exp_date must be today or later")


# DNS resolver (sync + async)
# @lru_cache(maxsize=1024)
def _sync_resolve(host: str) -> bool:
    """
    Pure DNS resolution. Returns True as long as the host
    has *any* A/AAAA record, regardless of which port is open.
    """
    try:
        # try IPv4 or IPv6 lookup
        socket.getaddrinfo(host, None)
        return True
    except socket.gaierror:
        return False

#ignore dns check for now
async def _async_resolve(host: str) -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_resolve, host)

async def validate_payload(
    payload: LongUrl = Body(
        ...,
        description="Payload for creating a short code",
        example={
            "url_link": "https://example.com/foo",
            "custom_slug": "my-slug",
            "exp_date": "2025-08-15",
            "password": "password"
        }
    )
) -> LongUrl:
   
    # URL HTTP Validation done in the LongUrl model
    parsed_url=payload.url_link
     
    # Async DNS check
    # if not await _async_resolve(parsed_url.host):
    #     raise HTTPException(400, f"Host {parsed_url.host!r} could not be resolved")
    
    payload.url_link=str(payload.url_link)
    
    # Validate the date if provided
    if payload.exp_date:
        await validate_date(payload.exp_date)

    # Return the validated payload
    return payload




async def validate_batch_payload(
    raw_items: List[Any] = Body(
        ...,
        description="Batch payload for creating multiple short URLs",
    )
) :
    """
    Returns (validated_items, failures). Raises 422 if all items failed.
    """
    validated: List[tuple[int,LongUrl]] = []
    failures: List[dict] = []

    for idx, raw in enumerate(raw_items):
        # --- schema validation ---
        try:
            item = LongUrl.model_validate(raw)
        except pydantic.ValidationError as ve:
            failures.append({
                "index": idx,
                "error_type": "schema",
                "details": ve.errors()[0]["msg"]
            })
            continue

        # --- domain validation ---
        try:
            good = await validate_payload(item)
        except HTTPException as he:
            failures.append({
                "index": idx,
                "error_type": "domain",
                "details": he.detail
            })
            continue

        validated.append((idx, good))
       

    # if *every* item failed, reject the batch
    if failures and not validated:
        raise HTTPException(
            status_code=422,
            detail={"failures": failures}
        )

    return validated, failures


# async def validate_batch_payload(
#     items: List[LongUrl] = Body(
#         ...,
#         description="Batch payload for creating multiple short URLs",
#     )
# ) -> List[LongUrl]:
#     validated = []
#     errors = []
#     for idx, item in enumerate(items):
#         try:
#             # call single‑item validator:
#             valid_item = await validate_payload(item)  
#             validated.append(valid_item)
#         except HTTPException as e:
#             # collect which index failed and why
#             errors.append({"index": idx, "detail": e.detail})
#     if errors:
#         raise HTTPException(422, detail={"batch_errors": errors})
#     return validated
