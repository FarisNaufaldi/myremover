"""rembg-backed background remover (loaded once, optimized for macOS/CPU)."""

from __future__ import annotations

import logging
import os
from typing import Optional

from PIL import Image

from background_removal.base import BackgroundRemover
from background_removal.postprocess import ensure_full_resolution, refine_alpha_edges
from config import get_settings

logger = logging.getLogger(__name__)


def _available_providers() -> list[str]:
    try:
        import onnxruntime as ort

        return list(ort.get_available_providers())
    except Exception:
        return ["CPUExecutionProvider"]


def _resolve_providers(preferred: str) -> tuple[str, list[str]]:
    """Pick ONNX ExecutionProviders. On Apple Silicon, CoreML is much faster."""
    preferred = (preferred or "").strip().lower()
    available = _available_providers()

    if preferred == "cuda" and "CUDAExecutionProvider" in available:
        return "cuda", ["CUDAExecutionProvider", "CPUExecutionProvider"]
    if preferred == "cpu":
        return "cpu", ["CPUExecutionProvider"]
    if preferred == "mps":
        # rembg uses ONNX Runtime; map "mps" preference to CoreML on Mac
        if "CoreMLExecutionProvider" in available:
            return "coreml", ["CoreMLExecutionProvider", "CPUExecutionProvider"]
        return "cpu", ["CPUExecutionProvider"]

    # Auto: CoreML (Apple) → CUDA → CPU
    if "CoreMLExecutionProvider" in available:
        return "coreml", ["CoreMLExecutionProvider", "CPUExecutionProvider"]
    if "CUDAExecutionProvider" in available:
        return "cuda", ["CUDAExecutionProvider", "CPUExecutionProvider"]
    return "cpu", ["CPUExecutionProvider"]


class RembgBackgroundRemover(BackgroundRemover):
    """
    High-quality background removal via rembg + ONNX Runtime.

    Speed notes:
    - CoreML EP used automatically on macOS when available
    - Full-resolution alpha-matting is expensive on large photos
      and is only applied when max(side) <= alpha_matting_max_side
    """

    name = "rembg"

    def __init__(self, model_name: Optional[str] = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.rembg_model
        self._session = None
        self._device = "cpu"
        self._settings = settings

    def load(self) -> None:
        from rembg import new_session

        self._device, providers = _resolve_providers(self._settings.inference_device)
        logger.info(
            "Loading rembg model '%s' (device=%s, providers=%s)...",
            self.model_name,
            self._device,
            providers,
        )
        try:
            self._session = new_session(self.model_name, providers=providers)
        except TypeError:
            self._session = new_session(self.model_name)
        except Exception as exc:
            if providers != ["CPUExecutionProvider"]:
                logger.warning(
                    "Provider %s failed (%s); falling back to CPU.", providers, exc
                )
                self._device = "cpu"
                self._session = new_session(
                    self.model_name, providers=["CPUExecutionProvider"]
                )
            else:
                raise
        self.name = f"rembg:{self.model_name}"
        logger.info("Model loaded: %s on %s", self.name, self._device)

    def is_loaded(self) -> bool:
        return self._session is not None

    def device(self) -> str:
        return self._device

    def _should_alpha_matte(self, size: tuple[int, int]) -> bool:
        if not self._settings.alpha_matting:
            return False
        max_side = max(size)
        limit = self._settings.alpha_matting_max_side
        if max_side > limit:
            logger.info(
                "Skipping alpha matting for %sx%s (max side %s > %s) for speed.",
                size[0],
                size[1],
                max_side,
                limit,
            )
            return False
        return True

    def remove_background(self, image: Image.Image) -> Image.Image:
        from rembg import remove

        if self._session is None:
            self.load()

        original_size = image.size
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        else:
            image = image.convert("RGBA").convert("RGB")

        kwargs = {
            "session": self._session,
            "force_return_bytes": False,
        }
        use_matting = self._should_alpha_matte(original_size)
        if use_matting:
            kwargs.update(
                {
                    "alpha_matting": True,
                    "alpha_matting_foreground_threshold": (
                        self._settings.alpha_matting_foreground_threshold
                    ),
                    "alpha_matting_background_threshold": (
                        self._settings.alpha_matting_background_threshold
                    ),
                    "alpha_matting_erode_size": self._settings.alpha_matting_erode_size,
                }
            )

        try:
            result = remove(image, **kwargs)
        except Exception as matting_err:
            if use_matting:
                logger.warning(
                    "Alpha matting failed (%s); retrying without matting.", matting_err
                )
                result = remove(image, session=self._session)
            else:
                raise

        if not isinstance(result, Image.Image):
            from io import BytesIO

            result = Image.open(BytesIO(result)).convert("RGBA")
        else:
            result = result.convert("RGBA")

        result = ensure_full_resolution(result, original_size)
        result = refine_alpha_edges(result)
        return result


_remover: Optional[RembgBackgroundRemover] = None


def get_remover() -> RembgBackgroundRemover:
    global _remover
    if _remover is None:
        _remover = RembgBackgroundRemover()
    return _remover


def load_model_on_startup() -> None:
    """Eager-load model at process start so first request isn't cold."""
    if os.getenv("SKIP_MODEL_LOAD", "").strip().lower() in {"1", "true", "yes"}:
        logger.info("SKIP_MODEL_LOAD set — model will load on first request.")
        return
    remover = get_remover()
    try:
        remover.load()
    except Exception:
        logger.exception(
            "Failed to load background-removal model at startup. "
            "It will retry on the first request."
        )
