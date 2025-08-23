from config.config import configSettgs
import asyncio
from typing import Any, Dict

MAX_UPLOAD_SIZE = 5 * 1024 * 1024   # 5 MB limit (adjust)
MEDIA_ROOT = configSettgs.MEDIA_ROOT
PROFILE_ROOT_PATH = configSettgs.PROFILE_IMG_PATH
ALLOWED_TOP_LEVEL = ("image",)      # allow only image/* Content-Type header (quick check)
CHUNK_SIZE = 1024 * 1024            # 1MB chunk reads

THUMB_ROOT_PATH = configSettgs.THUMBNAIL_IMG_PATH
BATCH_SIZE = 20
THUMB_SIZE = (300, 300)
PROCESSING_MARKER = "__PROCESSING__"


tasks_queue: asyncio.Queue[Dict[str, Any]] = None
tasks_executor: asyncio.Task | None = None
