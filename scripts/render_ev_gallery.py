"""Render 6 scenes × 7 methods × 7 EV ticks = 294 WebP tiles for the EV gallery.

Output: assets/gallery/scene_<id>/<method>_ev<+d>.webp
Idempotent: skips tiles whose output exists. Pass --force to overwrite.
"""
import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")  # MUST come before cv2
import cv2  # noqa: E402
import numpy as np  # noqa: E402

# Make `scripts.tonemap` importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.tonemap import display_image, median_normalize_factor  # noqa: E402

# user_study/HDR_Video_Project_Page/scripts/ -> user_study/
ROOT = Path(__file__).resolve().parent.parent.parent
HDR_ROOT = ROOT / "HDRStudyViewer"
SCENES_JSON = Path(__file__).resolve().parent.parent / "scenes.json"
OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "gallery"

# (label, folder relative to HDRStudyViewer/, file template)
COLUMNS: list[tuple[str, str, str]] = [
    ("GT",          "gt_hdr",                                        "test_{N}"),
    ("Ours",        "ours_results_best_apr20",                       "test_{N}_pred"),
    ("BracketDiff", "baselines/eval_testset_bracketdiff_uncond_512", "test_{N}"),
    ("HDRCNN",      "baselines/eval_testset_hdrcnn",                 "test_{N}"),
    ("SingleHDR",   "baselines/eval_testset_singlehdr",              "test_{N}"),
    ("LEDiff",      "baselines/eval_testset_lediff_full",            "test_{N}"),
    ("X2HDR",       "baselines/eval_sd21_pu21_hdr_predicted",        "test_{N}_pred"),
]

EV_TICKS = [-3, -2, -1, 0, 1, 2, 3]
WEBP_QUALITY = 88
MAX_EDGE = 1024


def load_hdr(folder: Path, stem: str) -> np.ndarray:
    """Load <folder>/<stem>.{exr,hdr} and return RGB float32."""
    for ext in (".exr", ".hdr"):
        p = folder / f"{stem}{ext}"
        if p.exists():
            img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
            if img is None:
                raise FileNotFoundError(f"cv2 returned None for {p}")
            if img.ndim == 2:
                img = np.stack([img] * 3, axis=-1)
            img = img.astype(np.float32)[..., :3]
            return img[..., ::-1].copy()  # BGR -> RGB
    raise FileNotFoundError(f"no {stem}.{{exr,hdr}} in {folder}")


def downscale_to_max_edge(rgb: np.ndarray, max_edge: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    edge = max(h, w)
    if edge <= max_edge:
        return rgb
    scale = max_edge / edge
    new_size = (int(round(w * scale)), int(round(h * scale)))
    return cv2.resize(rgb, new_size, interpolation=cv2.INTER_AREA)


def write_webp(out_path: Path, rgb_unit: np.ndarray, quality: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bgr = (np.clip(rgb_unit, 0.0, 1.0)[..., ::-1] * 255.0 + 0.5).astype(np.uint8)
    ok = cv2.imwrite(str(out_path), bgr, [cv2.IMWRITE_WEBP_QUALITY, quality])
    if not ok:
        raise IOError(f"cv2.imwrite failed for {out_path}")


def ev_signed_str(ev: int) -> str:
    """0 -> '+0', 3 -> '+3', -3 -> '-3'."""
    return f"{ev:+d}"


def render_one(folder: Path, stem: str, out_dir: Path, label: str,
               force: bool) -> int:
    """Render all 7 EV ticks for one (scene, method). Returns count written."""
    written = 0
    targets = {ev: out_dir / f"{label}_ev{ev_signed_str(ev)}.webp" for ev in EV_TICKS}
    if not force and all(p.exists() for p in targets.values()):
        return 0  # nothing to do

    rgb = load_hdr(folder, stem)
    rgb = downscale_to_max_edge(rgb, MAX_EDGE)
    factor = median_normalize_factor(rgb)  # FROZEN across EV ticks

    for ev in EV_TICKS:
        out_path = targets[ev]
        if out_path.exists() and not force:
            continue
        out = display_image(rgb, ev=float(ev), median_factor=factor)
        write_webp(out_path, out, WEBP_QUALITY)
        written += 1
    return written


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", type=Path, default=SCENES_JSON)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    scenes = json.loads(args.scenes.read_text())
    print(f"rendering {len(scenes)} scenes × {len(COLUMNS)} methods × "
          f"{len(EV_TICKS)} EV ticks = {len(scenes)*len(COLUMNS)*len(EV_TICKS)} tiles")

    total_written = 0
    for s in scenes:
        sid = s["id"]
        scene_dir = args.out / f"scene_{sid}"
        for label, folder_rel, tpl in COLUMNS:
            folder = HDR_ROOT / folder_rel
            stem = tpl.format(N=sid)
            try:
                n = render_one(folder, stem, scene_dir, label, args.force)
            except FileNotFoundError as e:
                print(f"  skip scene {sid} {label}: {e}")
                continue
            total_written += n
            if n:
                print(f"  scene {sid} {label}: wrote {n} tiles")

    print(f"done — wrote {total_written} new tiles to "
          f"{args.out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
