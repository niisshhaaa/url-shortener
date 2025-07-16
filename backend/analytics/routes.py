from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.analytics.repository import get_real_time_analytics
from db.dependencies import get_session
from db.schema import URL_SHORTENER

analytics_router=APIRouter()

@analytics_router.get("/real-time")
async def real_time_analytics(db_session:AsyncSession=Depends(get_session), limit:int=10, offset:int=0):
    data = await get_real_time_analytics(db_session,limit,offset)
    if not data:
        raise HTTPException(status_code=404, detail="Error in getting real time analytics")
    # return [row.to_dict() for row in data]
    return data


@analytics_router.get("/health")
async def health_check(db_session:AsyncSession=Depends(get_session)):
    try:
        stmt=text("SELECT 1")  
        await db_session.execute(stmt)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}