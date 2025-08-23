
import asyncio
import logging
from pathlib import Path
from typing import Tuple
from sqlalchemy import text
from backend.common.thumbnail_tasks import CLAIM_BATCH_SQL, MARK_FAILED_SQL, UPDATE_ROW_SQL, process_single_row_async
from backend.user.background_worker import process_thumbnail_task
from backend.user.constants import PROFILE_ROOT_PATH,BATCH_SIZE, MEDIA_ROOT, PROCESSING_MARKER, THUMB_ROOT_PATH, THUMB_SIZE
from backend.common.session import async_session,async_engine
from PIL import Image, UnidentifiedImageError

log = logging.getLogger("cron")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


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
        processed += await process_thumbnail_task(row_id, img_rel)
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