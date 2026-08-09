"""Background remover abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO
from typing import Tuple

from PIL import Image


class BackgroundRemover(ABC):
    """Interface for AI background-removal backends."""

    name: str = "base"

    @abstractmethod
    def load(self) -> None:
        """Load model weights into memory (once at startup)."""

    @abstractmethod
    def is_loaded(self) -> bool:
        ...

    @abstractmethod
    def device(self) -> str:
        ...

    @abstractmethod
    def remove_background(self, image: Image.Image) -> Image.Image:
        """Return an RGBA image with transparent background, same dimensions."""

    def remove_background_bytes(self, data: bytes) -> Tuple[Image.Image, Image.Image]:
        """Decode bytes → process → return (original RGB/RGBA, result RGBA)."""
        with Image.open(BytesIO(data)) as im:
            original = im.convert("RGBA")
            # Work on a copy with EXIF orientation applied
            from PIL import ImageOps

            oriented = ImageOps.exif_transpose(im)
            result = self.remove_background(oriented.convert("RGB"))
        return original.convert("RGBA"), result
