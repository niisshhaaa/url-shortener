#!/usr/bin/env python3
import asyncio
from typing import List
import httpx
from sqlalchemy import select
from config.config import configSettgs
from db.schema import URL_SHORTENER  
from db.db_connection import async_session

BASE_URL      = "http://localhost:8000"
API_PREFIX    = "/api/v2"
DATABASE_URL  = configSettgs.DATABASE_URL


async def fetch_short_codes(start_id: int, end_id: int) -> List[str]:
    """Load all short_codes whose primary key ID is in [start_id, end_id]."""
    async with async_session() as session:
        stmt = select(URL_SHORTENER.short_code).where(URL_SHORTENER.id >= start_id, URL_SHORTENER.id <= end_id)
        result = await session.execute(stmt)
        return [row[0] for row in result.all()]

async def warm_cache(codes: List[str]):
    """Hit the redirect endpoint for each code to populate Redis."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        for code in codes:
            url = f"{API_PREFIX}/redirect?short_code={code}"
            # follow_redirects=False means only hit the redirect endpoint
            r = await client.get(url, follow_redirects=False, timeout=10.0)
            if r.status_code == 307:
                print(f"[CACHE] warmed {code}")
            else:
                print(f"[SKIP ] {code} → {r.status_code}")

async def main():
    start_id = 141
    end_id   = 160

    codes = await fetch_short_codes(start_id, end_id)
    print(f"Found {len(codes)} codes; warming cache…")
    await warm_cache(codes)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
