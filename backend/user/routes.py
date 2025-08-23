
import asyncio
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends,status
from backend.user.constants import MAX_UPLOAD_SIZE, MEDIA_ROOT, PROFILE_ROOT_PATH
from backend.user.repository import save_user_avatar
from backend.user.utils import _stream_save_to_disk_sync,_verify_image_sync, user_hash
from db.dependencies import get_session
from PIL import UnidentifiedImageError
from config.config import configSettgs

SECRET_KEY=configSettgs.SUPER_SECRET_KEY

user_v3_router=APIRouter()

@user_v3_router.post("/me/upload-profile-img")
async def upload_profile_image(request:Request,file: UploadFile = File(), session = Depends(get_session)):
    
    user_identifier = request.state.user_identifier

    #* add more robust checks
    # cheap header check
    if not file.content_type or file.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only image uploads allowed")
    
    user_specific_path=f"{str(user_identifier.id)}_{user_hash(user_identifier.id,SECRET_KEY)}"
    user_dir=Path(PROFILE_ROOT_PATH)/user_specific_path
    dest_dir=Path(MEDIA_ROOT)/user_dir # deterministic for final path
    dest_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_dir / f"upload_{uuid.uuid4().hex}.tmp"  # unique temp 

    # prepare safe paths and temp file
    try:
        await asyncio.to_thread(_stream_save_to_disk_sync, file.file, tmp_path, MAX_UPLOAD_SIZE)
    except ValueError:
        # file too large
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File too large (max {MAX_UPLOAD_SIZE} bytes)")
    except Exception as e:
        # cleanup
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save upload") from e
    finally:
        # close starlette UploadFile internals
        await file.close()

    # verify image
    try:
        img_fmt=await asyncio.to_thread(_verify_image_sync, tmp_path)
    except UnidentifiedImageError:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Invalid image")
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Image verification failed")

    # ext_map = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
    # ext = ext_map.get(img_fmt, ".jpg")
    ext=".jpg"
    final_name = f"profile_{user_identifier.id}{ext}"
    final_path = dest_dir / final_name

    # atomic rename
    try:
        os.replace(tmp_path, final_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to finalize upload")
    
    print("rel path")
    # store relative path in DB: 
    rel_path = f"{user_specific_path}/{final_name}"
    
    await save_user_avatar(session, user_identifier.id, rel_path,final_path)

    return {"message": "uploaded", "image_path": rel_path}

