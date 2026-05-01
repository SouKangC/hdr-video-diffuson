"""Tone-map utilities matching the paper's existing pipeline.

The key invariant: when rendering a scene at multiple EV ticks, the
median-luminance normalization factor must be COMPUTED ONCE at EV=0
and reused for every other tick. Otherwise the post-Reinhard output
would re-anchor to mid-grey every tick and the EV slider would do
nothing visible. See `median_normalize_factor`.
"""
import numpy as np

MEDIAN_TARGET = 0.18


def luminance(rgb: np.ndarray) -> np.ndarray:
    """Rec.709 luminance from linear RGB."""
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def median_normalize_factor(rgb: np.ndarray, target: float = MEDIAN_TARGET) -> float:
    """Scalar gain that, applied to `rgb`, makes its median luminance == target.

    Computed once per (scene, method) at EV=0 and reused for every EV tick.
    Non-finite (Inf/NaN) luminance pixels are filtered out before the median,
    so frames with bad highlight values don't blacken the output.
    """
    Y = luminance(rgb)
    Y_pos = Y[np.isfinite(Y) & (Y > 1e-8)]
    if Y_pos.size == 0:
        return 1.0
    med = float(np.median(Y_pos))
    if med <= 1e-8:
        return 1.0
    return target / med


def reinhard_lum(rgb: np.ndarray) -> np.ndarray:
    """Reinhard tone-map on luminance (chromaticity preserved)."""
    Y = luminance(rgb)
    Y_new = Y / (1.0 + Y)
    scale = np.where(Y > 1e-8, Y_new / np.maximum(Y, 1e-8), 0.0)
    return np.clip(rgb * scale[..., None], 0.0, 1.0)


def srgb_encode(rgb: np.ndarray) -> np.ndarray:
    rgb = np.clip(rgb, 0.0, 1.0)
    return np.where(
        rgb <= 0.0031308,
        12.92 * rgb,
        1.055 * np.power(rgb, 1.0 / 2.4) - 0.055,
    )


def display_image(rgb: np.ndarray, ev: float = 0.0,
                  median_factor: float | None = None) -> np.ndarray:
    """End-to-end pre-display: optional EV gain → median normalize → Reinhard → sRGB.

    If `median_factor` is None it is computed from THIS image (use only at EV=0).
    For multi-tick rendering, compute it once at EV=0 and pass it back in.
    """
    if median_factor is None:
        median_factor = median_normalize_factor(rgb)
    scaled = rgb * (2.0 ** ev) * median_factor
    return srgb_encode(reinhard_lum(scaled))
