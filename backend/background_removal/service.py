"""Background-removal service: validation, processing, cleanup."""

from __future__ import annotations

import logging
import re
import secrets
import shutil
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, UnidentifiedImageError

from background_removal.rembg_provider import get_remover
from config import get_settings

logger = logging.getLogger(__name__)

ALLOWED_MIME = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
FORMAT_TO_MIME = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


@dataclass
class ProcessResult:
    png_bytes: bytes
    width: int
    height: int
    original_filename: str
    download_filename: str


class ImageValidationError(ValueError):
    pass


def _sanitize_filename(name: str) -> str:
    base = Path(name or "image").name
    base = re.sub(r"[^\w.\- ]+", "", base, flags=re.UNICODE).strip()
    base = base.replace(" ", "-")
    if not base or base in {".", ".."}:
        base = "image"
    # strip extension for stem
    stem = Path(base).stem[:80] or "image"
    return stem


def _detect_image(data: bytes) -> Tuple[str, str]:
    """Return (format_lower, mime). Raises ImageValidationError."""
    try:
        with Image.open(BytesIO(data)) as im:
            im.verify()
        with Image.open(BytesIO(data)) as im:
            fmt = (im.format or "").lower()
            if fmt == "jpg":
                fmt = "jpeg"
            mime = FORMAT_TO_MIME.get(fmt)
            if not mime:
                raise ImageValidationError(
                    "Unsupported image format. Please upload JPG, PNG, or WEBP."
                )
            # load fully to catch truncated images
            with Image.open(BytesIO(data)) as check:
                check.load()
            return fmt, mime
    except ImageValidationError:
        raise
    except UnidentifiedImageError as e:
        raise ImageValidationError(
            "Unsupported image format. Please upload JPG, PNG, or WEBP."
        ) from e
    except OSError as e:
        raise ImageValidationError(
            "Image appears to be corrupted or unreadable."
        ) from e


def validate_upload(
    data: bytes,
    filename: str,
    content_type: Optional[str],
) -> Tuple[str, str]:
    settings = get_settings()
    if not data:
        raise ImageValidationError("Empty file.")
    if len(data) > settings.max_upload_bytes:
        raise ImageValidationError(
            f"Image is too large. Please upload a smaller image "
            f"(max {settings.max_upload_mb} MB)."
        )

    ext = Path(filename or "").suffix.lower()
    if ext and ext not in ALLOWED_EXT:
        raise ImageValidationError(
            "Unsupported image format. Please upload JPG, PNG, or WEBP."
        )

    if content_type and content_type.split(";")[0].strip().lower() not in ALLOWED_MIME | {
        "application/octet-stream",
        "",
    }:
        # still try content validation — mime from browser can be wrong
        pass

    return _detect_image(data)


def process_image(data: bytes, filename: str) -> ProcessResult:
    """Full pipeline: validate → AI remove → refine → PNG bytes."""
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.result_dir.mkdir(parents=True, exist_ok=True)

    fmt, mime = validate_upload(data, filename, None)
    stem = _sanitize_filename(filename)
    token = secrets.token_hex(8)

    tmp_in: Optional[Path] = None
    try:
        # Temp storage for auditability during processing; cleaned always
        with tempfile.NamedTemporaryFile(
            delete=False,
            dir=settings.upload_dir,
            prefix=f"up_{token}_",
            suffix=f".{fmt}",
        ) as fh:
            fh.write(data)
            tmp_in = Path(fh.name)

        remover = get_remover()
        if not remover.is_loaded():
            remover.load()

        from PIL import ImageOps

        with Image.open(BytesIO(data)) as im:
            im = ImageOps.exif_transpose(im)
            work = im.convert("RGB")
            w, h = work.size
            result = remover.remove_background(work)

        if result.size != (w, h):
            result = result.resize((w, h), Image.Resampling.LANCZOS)

        buf = BytesIO()
        # compress_level=6 is a good speed/size tradeoff; optimize=True is very slow on large PNGs
        result.save(buf, format="PNG", compress_level=6, optimize=False)
        png_bytes = buf.getvalue()

        download_name = f"{stem}-no-bg.png"
        return ProcessResult(
            png_bytes=png_bytes,
            width=w,
            height=h,
            original_filename=filename or f"image.{fmt}",
            download_filename=download_name,
        )
    finally:
        if tmp_in and tmp_in.exists():
            try:
                tmp_in.unlink()
            except OSError:
                logger.warning("Failed to clean temp upload %s", tmp_in)


def cleanup_old_files(max_age_seconds: int = 3600) -> None:
    """Best-effort cleanup of leftover temp files."""
    import time

    settings = get_settings()
    now = time.time()
    for folder in (settings.upload_dir, settings.result_dir):
        if not folder.exists():
            continue
        for path in folder.iterdir():
            if path.name.startswith("."):
                continue
            try:
                age = now - path.stat().st_mtime
                if age > max_age_seconds:
                    if path.is_file():
                        path.unlink(missing_ok=True)
                    elif path.is_dir():
                        shutil.rmtree(path, ignore_errors=True)
            except OSError:
                continue
