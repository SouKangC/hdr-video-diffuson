import csv
import json
from pathlib import Path

from scripts.pick_hero_scenes import aggregate_win_rates, pick_top_n


def _write_csv(path: Path, rows: list[tuple[int, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["trial_index", "scene_id", "submode", "baseline",
                    "ours_position", "user_chose", "ours_preferred",
                    "shown_at", "responded_at"])
        for i, (sid, ours_pref) in enumerate(rows):
            w.writerow([i, sid, "gt_reference", "eval_testset_lediff_full",
                        "left", "left", ours_pref, "x", "y"])


def test_aggregate_win_rates_combines_all_csvs(tmp_path):
    p1 = tmp_path / "alice/20260101/results.csv"
    p2 = tmp_path / "bob/20260102/results.csv"
    _write_csv(p1, [(10, "true"), (10, "false"), (10, "true"), (20, "true")])
    _write_csv(p2, [(10, "true"), (20, "false")])

    rates = aggregate_win_rates(tmp_path)
    # scene 10: 2 wins / 3 trials in p1 + 1 win / 1 trial in p2 = 3/4 = 0.75
    # scene 20: 1 win / 1 trial in p1 + 0 wins / 1 trial in p2 = 1/2 = 0.5
    assert rates[10] == (3, 4)
    assert rates[20] == (1, 2)


def test_pick_top_n_filters_by_min_trials(tmp_path):
    rates = {1: (15, 16), 2: (3, 3), 3: (12, 16), 4: (14, 16), 5: (16, 16),
             6: (13, 16), 7: (11, 16), 8: (10, 16), 9: (9, 16), 10: (8, 16)}
    out = pick_top_n(rates, n=6, min_trials=15)
    # Scene 2 (3 trials) is excluded by min_trials filter.
    # Sort by win rate descending: 5 (1.0), 1 (0.9375), 4 (0.875), 6 (0.8125),
    # 3 (0.75), 7 (0.6875). Top 6 picked.
    assert [s["id"] for s in out] == [5, 1, 4, 6, 3, 7]
    assert [s["label"] for s in out] == ["A", "B", "C", "D", "E", "F"]
    assert out[0]["winRate"] == 1.0
