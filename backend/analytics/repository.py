from sqlalchemy import select
from db.schema import URL_SHORTENER

async def get_real_time_analytics(session,limit,offset):
    result=await session.execute(
           select(URL_SHORTENER).order_by(URL_SHORTENER.created_at.desc()).limit(limit)
        )
    # statement2=select(func.count(URL_SHORTENER.short_code).label("total_urls"))
    # result2=await session.execute(statement2)
    # print(result2.fetchone()) #(10001057,)
    scalars=result.scalars()
    result=scalars.all()
    print("scalars result" , scalars) # <sqlalchemy.engine.result.ScalarResult object at 0x000001CDAE829680>
    print("result all",result) #[<db.schema.URL_SHORTENER object at 0x000001CDAEE30C10>, <db.schema.URL_SHORTENER object at 0x000001CDAEA072D0>, ...
    return result