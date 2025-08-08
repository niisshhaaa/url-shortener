

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from backend.v3.utils.urls_utils import parse_year_filter
from db.schema import URL_SHORTENER
from sqlalchemy.ext.asyncio import AsyncSession


async def get_urls(
    session: AsyncSession,
    user_id: int,
    limit: int,
    after_cursor: Optional[datetime],
    time_filter: Optional[int]
):
    start, end = parse_year_filter(time_filter)
    stmt = (
        select(URL_SHORTENER)
        .where(
            URL_SHORTENER.user_id == user_id,
            URL_SHORTENER.deleted_at.is_(None),
            URL_SHORTENER.created_at >= start,
            URL_SHORTENER.created_at <= end,
        )
    )

    if after_cursor:
        # Fetch items older than the cursor for descending order paging
        stmt = stmt.where(URL_SHORTENER.created_at < after_cursor)

    # Order by newest first
    stmt = stmt.order_by(URL_SHORTENER.created_at.desc()).limit(limit)
    res = await session.execute(stmt)
    rows= res.scalars().all()
    return [
        {
            "id":           row.id,
            "original_url": row.original_url,
            "short_code":   row.short_code,
            "created_at":   row.created_at,
            "visit_cnt":    row.visit_cnt,
            "expiry_date":  row.expiry_date,
            "password":  row.password
        }
        for row in rows
    ]

# we can also return count along with year if needed 
async def get_earliest_year(session: AsyncSession, user_id: int) -> Optional[int]:
    stmt = (
        select(func.min(URL_SHORTENER.created_at))
        .where(
            URL_SHORTENER.user_id == user_id,
            URL_SHORTENER.deleted_at.is_(None)
        )
    )
    res = await session.execute(stmt)
    min_ts = res.scalar()
    return min_ts.year if min_ts else None