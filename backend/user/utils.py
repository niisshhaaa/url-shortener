import hashlib
import hmac
import time
from pathlib import Path
from backend.user.constants import CHUNK_SIZE
from PIL import Image

def _stream_save_to_disk_sync(src_file, tmp_path: Path, max_size: int, chunk_size: int = CHUNK_SIZE):
    start=time.time()
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with open(tmp_path, "wb") as w:
        while True:
            chunk = src_file.read(chunk_size)
            if not chunk:
                break
            w.write(chunk)
            total += len(chunk)
            if max_size and total > max_size:
                try: w.close()
                except: pass
                tmp_path.unlink(missing_ok=True)
                raise ValueError("file too large")
    end=time.time()
    print(f"Time taken to save file to disk: {(end-start)*1000} milliseconds")
    return total

def _verify_image_sync(tmp_path: Path) -> str:
    start=time.time()
    with Image.open(tmp_path) as img:
        img.verify()
        fmt = img.format or "JPEG"
    end=time.time()
    print(f"Time taken to verify image: {(end-start)*1000} milliseconds")
    return fmt.upper()

def user_hash(user_id: int, secret) -> str:
    return hmac.new(secret.encode(), str(user_id).encode(), hashlib.sha256).hexdigest()[:16]