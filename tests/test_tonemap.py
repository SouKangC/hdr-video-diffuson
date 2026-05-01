import numpy as np
import pytest
from scripts.tonemap import (
    luminance, median_normalize_factor, reinhard_lum, srgb_encode, display_image,
)


def test_luminance_is_rec709():
    rgb = np.array([[[1.0, 0.0, 0.0]]], dtype=np.float32)  # red
    assert luminance(rgb)[0, 0] == pytest.approx(0.2126, rel=1e-4)


def test_median_normalize_factor_returns_scalar_for_unit_grey():
    # An image of constant 0.18 grey already has median luminance 0.18,
    # so the factor should be 1.0.
    rgb = np.full((4, 4, 3), 0.18, dtype=np.float32)
    factor = median_normalize_factor(rgb, target=0.18)
    assert factor == pytest.approx(1.0, rel=1e-5)


def test_median_factor_frozen_across_ev_changes_brightness():
    """The whole point: applying the same median factor at multiple EV
    multipliers must produce monotonically brighter post-Reinhard images."""
    rng = np.random.default_rng(0)
    rgb = rng.uniform(0.0, 4.0, (32, 32, 3)).astype(np.float32)
    factor = median_normalize_factor(rgb, target=0.18)

    means = []
    for ev in (-2, -1, 0, 1, 2):
        gain = 2.0 ** ev
        scaled = rgb * gain * factor
        out = srgb_encode(reinhard_lum(scaled))
        means.append(float(out.mean()))

    # Strictly increasing brightness with EV.
    assert all(means[i] < means[i + 1] for i in range(len(means) - 1)), means


def test_display_image_clips_to_unit_range():
    rng = np.random.default_rng(1)
    rgb = rng.uniform(0.0, 100.0, (8, 8, 3)).astype(np.float32)
    out = display_image(rgb)
    assert out.min() >= 0.0
    assert out.max() <= 1.0


def test_srgb_encode_known_values():
    rgb = np.array([[[0.0, 0.5, 1.0]]], dtype=np.float32)
    out = srgb_encode(rgb)
    assert out[0, 0, 0] == pytest.approx(0.0, abs=1e-5)
    assert out[0, 0, 1] == pytest.approx(0.7354, abs=1e-3)
    assert out[0, 0, 2] == pytest.approx(1.0, abs=1e-5)
