import json,aiofiles
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger("blacklist")
BLACKLIST_PATH = Path("config/blacklist.json")


async def load_blacklist(blocked_keys) -> None:
    """
    Load the blacklist JSON into the global `blocked_keys` set.
    Expects the file to contain a JSON array of strings.
    """
    try:
        async with aiofiles.open(BLACKLIST_PATH, mode="r") as f:
            raw = await f.read()
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("Expected a JSON array of strings")
        # Filter to strings only
        keys = {k for k in data if isinstance(k, str)}
        blocked_keys.clear()
        blocked_keys.update(keys)
        logger.info(f"Loaded {len(blocked_keys)} blocked API keys.")
    except FileNotFoundError:
        logger.warning(f"{BLACKLIST_PATH} not found; no keys blocked.")
    except (json.JSONDecodeError, ValueError):
        # malformed → keep the old set
        pass
