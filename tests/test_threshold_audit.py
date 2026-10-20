import json
import math
import unittest
from datetime import date, timedelta
from pathlib import Path

from data_contract_observatory.ecb import parse_csv
from data_contract_observatory.threshold_audit import (
    build_threshold_audit,
    episodes,
    gaussian_two_sided,
    robust_scores,
)

ROOT = Path(__file__).parents[1]


def _series(shock_at: int | None = None) -> tuple[list[date], list[float]]:
    start = date(2020, 1, 1)
    dates = [start + timedelta(days=i) for i in range(300)]
    values = [1.0]
    for i in range(1, 300):
        step = 0.001 * (1 if i % 2 else -1) * (1 + (i % 7) / 10)
        values.append(values[-1] * math.exp(step))
    if shock_at is not None:
        values[shock_at] = values[shock_at - 1] * math.exp(0.05)
    return dates, values


class ThresholdAuditTests(unittest.TestCase):
    def test_gaussian_tail_matches_known_values(self) -> None:
        self.assertAlmostEqual(gaussian_two_sided(1.96), 0.05, places=3)
        self.assertAlmostEqual(gaussian_two_sided(3.0), 0.0027, places=4)

    def test_episode_grouping(self) -> None:
        days = [date(2020, 1, 1), date(2020, 1, 2), date(2020, 3, 1)]
        self.assertEqual(episodes(days), 2)
        self.assertEqual(episodes([]), 0)

    def test_planted_shock_is_the_only_extreme_score(self) -> None:
        dates, values = _series(shock_at=250)
        scores = robust_scores(dates, values)
        flagged = [day for day, score in scores if abs(score) >= 6]
        self.assertIn(dates[250], flagged)
        self.assertTrue(set(flagged) <= {dates[250], dates[251]})  # the reversal also fires

    def test_constant_baseline_yields_infinite_score_for_a_move(self) -> None:
        dates = [date(2020, 1, 1) + timedelta(days=i) for i in range(70)]
        values = [1.0] * 69 + [1.1]
        self.assertTrue(math.isinf(robust_scores(dates, values)[-1][1]))
        self.assertEqual(robust_scores(dates, [1.0] * 70)[-1][1], 0.0)

    def test_frozen_threshold_six_count_matches_the_v1_evaluation(self) -> None:
        text = (ROOT / "data/ecb-exr-usd-eur-to-2026-08-13.csv").read_text(encoding="utf-8-sig")
        _, rows = parse_csv(text)
        eligible = [row for row in rows if row.get("TIME_PERIOD") and row.get("OBS_VALUE")]
        audit = build_threshold_audit(
            [date.fromisoformat(row["TIME_PERIOD"]) for row in eligible],
            [float(row["OBS_VALUE"]) for row in eligible],
        )
        frozen = json.loads((ROOT / "reports/v1-evaluation.json").read_text(encoding="utf-8"))
        at_six = next(item for item in audit["thresholds"] if item["threshold"] == 6.0)
        self.assertEqual(audit["evaluated_days"], frozen["retrospective_replay"]["replay_count"])
        self.assertEqual(at_six["signals"], frozen["retrospective_replay"]["review_signal_count"])
        stored = json.loads(
            (ROOT / "reports/post-release-threshold-audit.json").read_text(encoding="utf-8")
        )
        self.assertEqual(stored, json.loads(json.dumps(audit)))

    def test_site_table_matches_the_audit_file(self) -> None:
        stored = json.loads(
            (ROOT / "reports/post-release-threshold-audit.json").read_text(encoding="utf-8")
        )
        copy = json.loads((ROOT / "site/data/threshold-audit.json").read_text(encoding="utf-8"))
        self.assertEqual(stored, copy)
        page = (ROOT / "site/index.html").read_text(encoding="utf-8")
        for row in stored["thresholds"]:
            self.assertIn(f"<td>{row['signals']}</td>", page)
            self.assertIn(f"<td>{row['episodes']}</td>", page)


if __name__ == "__main__":
    unittest.main()
