from pathlib import Path
from backend.__init__ import logger
from backend.common.thumbnail_tasks import process_thumbnail_task
from backend.user.constants import MEDIA_ROOT, THUMB_ROOT_PATH
from backend.common.session import async_session
from backend.user import constants



async def thumbnail_worker_loop():
    logger.info("Thumbnail worker started, waiting for tasks...")
    processed=0
    while True:
        try:
            task = await constants.tasks_queue.get()
            if task is None:
                # sentinel to shutdown
                logger.info("Thumbnail worker shutting down")
                break

            user_id = task["user_id"]
            media_id = task["media_id"]
            rel_path = task["rel_path"]

            logger.info("[worker] picked task user=%s row=%s", user_id, media_id)

            processed += await process_thumbnail_task(media_id, user_id,rel_path,async_session)
        except Exception:
            logger.exception("[worker] unexpected error handling task: %s", task)
            # avoid losing the item forever; mark done to prevent blocking if you've chosen to
            try:
                constants.tasks_queue.task_done()
            except Exception:
                pass

    logger.info("[worker] processed task user=%s row=%s processed=%s", user_id, media_id, processed)
