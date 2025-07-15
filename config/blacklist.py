import json
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger("blacklist")
BLACKLIST_PATH = Path("config/blacklist.json")


def load_blacklist(blocked_keys) -> None:
    """
    Load the blacklist JSON into the global `blocked_keys` set.
    Expects the file to contain a JSON array of strings.
    """
    try:
        raw = BLACKLIST_PATH.read_text()
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
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {BLACKLIST_PATH}: {e}")
    except ValueError as e:
        logger.error(f"Bad format in {BLACKLIST_PATH}: {e}")