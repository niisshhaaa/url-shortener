
from sqlalchemy import select
from db.schema import Users,TierLevel

async def get_idntier_api_key(api_key,session):
    stmt=select(Users.id,Users.tier_level).where(Users.api_key==api_key)
    result=await session.execute(stmt)
    return result.first()