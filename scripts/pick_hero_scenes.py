"""Aggregate per-scene Ours-win rates from study CSVs and pick top-N hero scenes.

Reads HDRStudyViewer/results/participants/<name>/<date>/*.csv and writes
scenes.json with the top-6 highest-win-rate scenes (filtered to scenes with
>=15 trials so noisy small-sample scenes don't slip in).

Usage:  python scripts/pick_hero_scenes.py [--participants-root PATH]
"""
import argparse
import csv
import json
import string
from collections import defaultdict
from pathlib import Path

# user_study/HDR_Video_Project_Page/scripts/ -> user_study/
ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PARTICIPANTS_ROOT = ROOT / "HDRStudyViewer" / "results" / "participants"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "scenes.json"


def aggregate_win_rates(participants_root: Path) -> dict[int, tuple[int, int]]:
    """Return {scene_id: (ours_wins, total_trials)} aggregated across every CSV."""
    counts: dict[int, list[int]] = defaultdict(lambda: [0, 0])  # [wins, total]
    for csv_path in participants_root.rglob("*.csv"):
        with csv_path.open() as f:
            for row in csv.DictReader(f):
                try:
                    sid = int(row["scene_id"])
                except (KeyError, ValueError):
                    continue
                counts[sid][1] += 1
                if row.get("ours_preferred", "").lower() == "true":
                    counts[sid][0] += 1
    return {s: (w, t) for s, (w, t) in counts.items()}


def pick_top_n(rates: dict[int, tuple[int, int]], n: int = 6,
               min_trials: int = 15) -> list[dict]:
    """Filter by min_trials, sort by win rate descending, take top n, label A..."""
    eligible = [(sid, w, t) for sid, (w, t) in rates.items() if t >= max(1, min_trials)]
    eligible.sort(key=lambda r: (-(r[1] / r[2]), r[0]))  # ties broken by lowest sid
    out = []
    labels = string.ascii_uppercase[:n]
    if n > len(labels):
        raise ValueError(f"n={n} exceeds 26 (max single-letter labels A..Z)")
    for label, (sid, w, t) in zip(labels, eligible[:n]):
        out.append({"id": sid, "label": label, "winRate": round(w / t, 4),
                    "wins": w, "trials": t})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--participants-root", type=Path,
                    default=DEFAULT_PARTICIPANTS_ROOT)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--min-trials", type=int, default=15)
    args = ap.parse_args()

    rates = aggregate_win_rates(args.participants_root)
    scenes = pick_top_n(rates, n=args.n, min_trials=args.min_trials)
    args.out.write_text(json.dumps(scenes, indent=2) + "\n")
    print(f"wrote {args.out.relative_to(ROOT)} ({len(scenes)} scenes)")
    for s in scenes:
        print(f"  {s['label']}: scene {s['id']:>3} - "
              f"{s['wins']}/{s['trials']} = {s['winRate']*100:.1f}%")


if __name__ == "__main__":
    main()
