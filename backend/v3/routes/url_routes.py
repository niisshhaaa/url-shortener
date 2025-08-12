from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.v3.repository.urls_repo import get_earliest_year, get_urls
from db.dependencies import get_session

urls_v3_router = APIRouter()

@urls_v3_router.get("/urls", response_model=Dict[str, Any])
async def get_all_urls_for_user(
    request: Request,
    db_session: AsyncSession = Depends(get_session),
    limit: int = Query(10, ge=1),
    after_cursor: Optional[datetime] = Query(None),
    time_filter: Optional[int] = Query(None, description="Year, e.g. 2025")
) -> Dict[str, Any]:
    """
    Cursor-based paging + year filter:
      - `limit`        : page size
      - `after_cursor` : ISO timestamp cursor (last item of previous page)
      - `time_filter`  : calendar year to filter by (defaults to current year)

    Returns:
    {
      "data": [...],
      "meta": {
         "limit": int,
         "after": str | null,       # next cursor
         "earliest_year": int,      # year of the oldest URL ever
         "time_filter": int,        # the year filter used
      }
    }
    """
    user = request.state.user_identifier
    user_id = user.id

    earliest_year = await get_earliest_year(db_session, user_id)
    if earliest_year is None:
        return {"data": [], "meta": {"after": None,"earliest_year": None}}

    urls = await get_urls(db_session, user_id, limit, after_cursor, time_filter)

    # Determine next cursor from last item's created_at or current set
    next_cursor = urls[-1]["created_at"].isoformat() if urls else None

    return {
        "data": urls,
        "meta": {
            "after": next_cursor,
            "earliest_year": earliest_year,
        }
    }

