
from fastapi import HTTPException,status
from sqlalchemy import update
from db.schema import Users,UserMedia
from sqlalchemy.exc import IntegrityError

# to keep insert idempotent under double clicks(concurrency) by same user use following save styles --
# at frontend level show loading spinner so user cannot do multiple clicks at once.
# on conflict do update(unique constraint required)
# select and insert (if row exists don’t insert , otherwise add)(db level lock per key )
# select and insert (retry on integrity error)

async def save_user_avatar(session, user_id: int, image_path: str,final_path:str):
    
    try:
        session.add(UserMedia(user_id=user_id, profile_img_path=image_path))
        await session.commit()
    except IntegrityError:
        await session.rollback()
        stmt = (
            update(UserMedia)
            .where(UserMedia.user_id == user_id)
            .values(
                profile_img_path=image_path
            )
        )
        await session.execute(stmt)
        await session.commit()
    except Exception as e:
        print("save error",e)
        final_path.unlink(missing_ok=True)
        await session.rollback()
        #log e 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save avatar")