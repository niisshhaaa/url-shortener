
import asyncio
import logging
from pathlib import Path
from typing import Tuple
from sqlalchemy import text
from backend.user.constants import PROFILE_ROOT_PATH,BATCH_SIZE, MEDIA_ROOT, PROCESSING_MARKER, THUMB_ROOT_PATH, THUMB_SIZE
from backend.cron.session import async_session,async_engine
from PIL import Image, UnidentifiedImageError

log = logging.getLogger("cron")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# SQL (example)
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
UPDATE_ROW_SQL = text("UPDATE user_media SET thumbnail_img_path = :thumb_path WHERE id = :id")
MARK_FAILED_SQL = text("UPDATE user_media SET thumbnail_img_path = NULL WHERE id = :id")


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


async def claim_and_process_batch(async_session_maker, limit: int = BATCH_SIZE):
    # 1) Claim a small batch atomically (session tied to THIS engine/loop)
    async with async_session_maker() as session:
        result = await session.execute(CLAIM_BATCH_SQL, {"limit": limit, "marker": PROCESSING_MARKER})
        rows = result.all()
        await session.commit()

    if not rows:
        log.info("No rows to process")
        return 0

    processed = 0
    for row in rows:
        row_id, img_rel = row[0], row[1]
        try:
            _, rel_thumb = await process_single_row_async(row_id, img_rel)
            async with async_session_maker() as session:
                await session.execute(UPDATE_ROW_SQL, {"thumb_path": rel_thumb, "id": row_id})
                await session.commit()
            processed += 1
            log.info("Processed %s -> %s", row_id, rel_thumb)
        except FileNotFoundError:
            log.exception("Missing file for %s, clearing marker", row_id)
            async with async_session_maker() as session:
                await session.execute(MARK_FAILED_SQL, {"id": row_id})
                await session.commit()
        except UnidentifiedImageError:
            log.exception("Bad image for %s, clearing marker", row_id)
            async with async_session_maker() as session:
                await session.execute(MARK_FAILED_SQL, {"id": row_id})
                await session.commit()
        except Exception:
            log.exception("Unexpected error for %s, clearing marker", row_id)
            async with async_session_maker() as session:
                await session.execute(MARK_FAILED_SQL, {"id": row_id})
                await session.commit()

    return processed


async def cron_worker(async_session):
    while True:
        try:
            n = await claim_and_process_batch(async_session)
            log.info("Batch complete, processed=%d", n)
        except Exception:
            print("batch run failed")
            log.exception("Batch run failed")
        await asyncio.sleep(60)


# --- start the cron in a dedicated thread+loop+engine ---
def start_cron_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(cron_worker(async_session))
    except Exception:
        print("cron thread failed")
        log.exception("Cron thread failed")
    finally:
        loop.run_until_complete(async_engine.dispose())
        loop.close()