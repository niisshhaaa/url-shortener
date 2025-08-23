import asyncio
from pathlib import Path
from typing import Tuple
from sqlalchemy import text
from backend.user.constants import PROFILE_ROOT_PATH, MEDIA_ROOT, THUMB_ROOT_PATH, THUMB_SIZE
from PIL import Image, UnidentifiedImageError
from backend.common.session import async_session
from backend.__init__ import logger

CLAIM_BATCH_SQL = text("""
WITH cte AS (
  SELECT id
  FROM user_media
  WHERE profile_img_path IS NOT NULL AND (thumbnail_img_path IS NULL)
  FOR UPDATE SKIP LOCKED
  LIMIT :limit
)
UPDATE user_media
SET thumbnail_img_path = :marker
FROM cte
WHERE user_media.id = cte.id
RETURNING user_media.id, user_media.profile_img_path
""")
UPDATE_ROW_SQL = text("UPDATE user_media SET thumbnail_img_path = :thumb_path WHERE id = :id AND user_id =:user_id")
MARK_FAILED_SQL = text("UPDATE user_media SET thumbnail_img_path = NULL WHERE id = :id AND user_id =:user_id")
SELECT_MEDIA_ID=text("SELECT user_media.id FROM user_media WHERE id=:id")

# --- blocking helpers (run in threads) ---
def _open_and_resize_sync(src_path: Path, size=(300,300)):
    with Image.open(src_path) as im:
        # do the resize/crop here (release GIL inside Pillow for heavy ops)
        im.thumbnail((max(size), max(size)), Image.LANCZOS)
        w,h = im.size
        tw,th = size
        left = max(0, (w - tw)//2)
        top = max(0, (h - th)//2)
        cropped = im.crop((left, top, left+tw, top+th))
        # return a copy (safe to use outside file context)
        return cropped.copy(), (im.format or "JPEG")

def _save_atomic_sync(img: Image.Image, dest: Path, fmt="JPEG", quality=85):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    img.save(tmp, format=fmt, quality=quality, optimize=True)
    tmp.replace(dest)


# --- processing logic (async, but offloads blocking parts to threads) ---
async def process_single_row_async(row_id: int, image_rel: str) -> Tuple[int, str]:
    src = MEDIA_ROOT / Path(PROFILE_ROOT_PATH) / image_rel
    # log(src, "processing row", row_id)
    if not src.exists():
        raise FileNotFoundError("source missing: %s" % src)

    # blocking open+resize in thread
    thumb_img, fmt = await asyncio.to_thread(_open_and_resize_sync, src, THUMB_SIZE)

    # choose thumbnail path
    rel_thumb=f"{row_id}/thumb_{row_id}.jpg"
    abs_thumb = MEDIA_ROOT / Path(THUMB_ROOT_PATH) / rel_thumb

    # save in thread (blocking)
    await asyncio.to_thread(_save_atomic_sync, thumb_img, abs_thumb, "JPEG", 85)

    return row_id, str(rel_thumb)


async def process_thumbnail_task(row_id,user_id,img_rel,async_session):
    processed = 0
    async with async_session() as session:
        res=await session.execute(SELECT_MEDIA_ID,{"id":row_id})
    if not res:
        logger.error("cannot process object with id None")
        return 
    try:
        _, rel_thumb = await process_single_row_async(row_id, img_rel)
        async with async_session() as session:
            await session.execute(UPDATE_ROW_SQL, {"thumb_path": rel_thumb, "id": row_id,"user_id":user_id})
            await session.commit()
        processed = 1
        logger.info("Processed %s -> %s", row_id, rel_thumb)
        return processed
    except FileNotFoundError:
        logger.exception("Missing file for %s, clearing marker", row_id)
        async with async_session() as session:
            await session.execute(MARK_FAILED_SQL, {"id": row_id,"user_id":user_id})
            await session.commit()
    except UnidentifiedImageError:
        logger.exception("Bad image for %s, clearing marker", row_id)
        async with async_session() as session:
            await session.execute(MARK_FAILED_SQL, {"id": row_id,"user_id":user_id})
            await session.commit()
    except Exception:
        logger.exception("Unexpected error for %s, clearing marker", row_id)
        async with async_session() as session:
            await session.execute(MARK_FAILED_SQL, {"id": row_id,"user_id":user_id})
            await session.commit()