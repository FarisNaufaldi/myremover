"""Alpha mask refinement and halo reduction.

These post-processing steps keep soft edges (hair / fur) while reducing the
common white/black fringe that appears around hard cutouts.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def refine_alpha_edges(rgba: Image.Image) -> Image.Image:
    """Light edge cleanup without hard thresholding the whole mask."""
    if rgba.mode != "RGBA":
        rgba = rgba.convert("RGBA")

    arr = np.array(rgba, dtype=np.float32)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3] / 255.0

    # Soft crush only near-zero/near-one values — preserve mid-alpha (hair)
    alpha = np.where(alpha < 0.02, 0.0, alpha)
    alpha = np.where(alpha > 0.98, 1.0, alpha)

    # Gentle decontamination on semi-transparent edge pixels:
    # pull fringe colors toward premultiplied interior color estimate.
    fringe = (alpha > 0.05) & (alpha < 0.92)
    if fringe.any():
        # Approximate interior color as alpha-weighted average of opaque pixels
        solid = alpha > 0.85
        if solid.any():
            # Local-ish fallback: for each fringe pixel use global solid mean
            # (fast) then blend slightly — reduces white halo on light BG
            mean_rgb = rgb[solid].mean(axis=0)
            strength = (1.0 - alpha[fringe]) * 0.55
            rgb[fringe] = (
                rgb[fringe] * (1.0 - strength[:, None])
                + mean_rgb[None, :] * strength[:, None]
            )

    out = np.empty_like(arr)
    out[:, :, :3] = np.clip(rgb, 0, 255)
    out[:, :, 3] = np.clip(alpha * 255.0, 0, 255)
    result = Image.fromarray(out.astype(np.uint8), "RGBA")

    # Very light blur on alpha channel only for anti-aliased edges
    r, g, b, a = result.split()
    a = a.filter(ImageFilter.GaussianBlur(radius=0.4))
    return Image.merge("RGBA", (r, g, b, a))


def ensure_full_resolution(result: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """Upsample mask/result to original resolution if the model downsized it."""
    if result.size == target_size:
        return result
    return result.resize(target_size, Image.Resampling.LANCZOS)
