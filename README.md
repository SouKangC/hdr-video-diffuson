# HDR Video Diffusion — Project Page

Static project page for *Single-Shot HDR Recovery via a Video Diffusion Prior*. Plain HTML + CSS + vanilla JS, no build step.

## Local preview

```bash
cd user_study/HDR_Video_Project_Page
python3 -m http.server 8000
# open http://localhost:8000/
```

## Regenerate assets

Requires `opencv-python` and `numpy`:

```bash
pip install opencv-python numpy
python scripts/pick_hero_scenes.py    # writes scenes.json
python scripts/render_ev_gallery.py   # writes assets/gallery/**/*.webp (~50 min)
```

Re-runs are idempotent; pass `--force` to overwrite.

## Layout

- `index.html` — single page, ~12 sections.
- `style.css` — Jon-Barron-style minimal CSS.
- `js/ev-gallery.js` — interactive method picker + EV slider (declarative, reads `data-*` attrs).
- `scripts/tonemap.py` — shared tone-map utilities (median-luminance frozen across EV ticks).
- `assets/gallery/scene_<id>/<method>_ev<+d>.webp` — 6 × 7 × 7 = 294 precomputed tiles.

## Deploy (when ready)

```bash
git init && git add -A && git commit -m "initial"
gh repo create hdr-video-diffusion-page --public --source=. --push
gh api -X POST repos/{owner}/hdr-video-diffusion-page/pages -f build_type=workflow
```
