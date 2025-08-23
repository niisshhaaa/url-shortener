
from fastapi import HTTPException,status
from sqlalchemy import update
from db.schema import Users,UserMedia
from sqlalchemy.exc import IntegrityError

# to keep insert idempotent under double clicks(concurrency) by same user use following save styles --
# at frontend level show loading spinner so user cannot do multiple clicks at once.
# on conflict do update(unique constraint required)
# select and insert (if row exists don’t insert , otherwise add)(db level lock per key )
# select and insert (retry on integrity error)

# for now only profile image exists for 1 user . there is a unique constraint on user_id fkey in user_media
async def save_user_avatar(session, user_id: int, image_path: str,final_path:str):
    new=UserMedia(user_id=user_id, profile_img_path=image_path)
    session.add(new)
    try:
        # flush sends INSERT to DB so new.id is populated (but not committed)
        await session.flush()
        media_id = new.id
        await session.commit()
        return media_id
    except IntegrityError:   
        await session.rollback()
        stmt = (
            update(UserMedia)
            .where(UserMedia.user_id == user_id)    # since one user has only one profile allowed and user id fkey is unique .
            .values(
                profile_img_path=image_path,
                thumbnail_img_path=None
            ).returning(UserMedia.id)
        )
        res=await session.execute(stmt)
        res=res.first()[0]
        await session.commit()
        print(res)
        return res
    except Exception as e:
        print("save error",e)
        final_path.unlink(missing_ok=True)
        await session.rollback()
        #log e 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save avatar")