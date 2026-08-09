"""Background removal API routes."""

from __future__ import annotations

import base64
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from background_removal.rembg_provider import get_remover
from background_removal.service import ImageValidationError, process_image
from config import get_settings
from deps import require_auth
from models import User
from schemas import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["background-removal"])


@router.post("/remove-background", response_model=ApiResponse[dict])
async def remove_background(
    file: UploadFile = File(...),
    _: User = Depends(require_auth),
):
    settings = get_settings()
    raw = await file.read()

    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Image is too large. Please upload a smaller image "
                f"(max {settings.max_upload_mb} MB)."
            ),
        )

    try:
        result = process_image(raw, file.filename or "image.png")
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception:
        logger.exception("Background removal failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while processing your image. Please try again.",
        ) from None

    b64 = base64.b64encode(result.png_bytes).decode("ascii")
    return ApiResponse(
        success=True,
        data={
            "width": result.width,
            "height": result.height,
            "filename": result.download_filename,
            "original_filename": result.original_filename,
            "mime_type": "image/png",
            "image_base64": b64,
            "size_bytes": len(result.png_bytes),
        },
    )


@router.get("/health", response_model=ApiResponse[dict])
def health():
    remover = get_remover()
    return ApiResponse(
        success=True,
        data={
            "status": "ok",
            "model_loaded": remover.is_loaded(),
            "model_name": remover.name,
            "device": remover.device() if remover.is_loaded() else "unloaded",
        },
    )
