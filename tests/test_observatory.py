from __future__ import annotations

import json
import math
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from data_contract_observatory.contract import (
    easter_sunday,
    is_expected_publication_day,
    latest_expected_day,
)
from data_contract_observatory.ecb import parse_csv
from data_contract_observatory.evaluate import evaluate, transport_failure
from data_contract_observatory.ledger import compare, normalize, record
from data_contract_observatory.validation import evaluate_suite, retrospective_replay

FIXTURE = Path(__file__).parent / "fixtures" / "ecb_valid.csv"
BERLIN = ZoneInfo("Europe/Berlin")


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.columns, self.rows = parse_csv(FIXTURE.read_text(encoding="utf-8"))

    def test_valid_fixture_passes_before_same_day_cutoff(self) -> None:
        report = evaluate(
            self.columns,
            self.rows,
            now=datetime(2026, 8, 13, 17, 0, tzinfo=BERLIN),
        )
        self.assertEqual(report.contract_status, "pass")
        self.assertEqual(report.review_status, "clear")

    def test_missing_required_column_fails(self) -> None:
        report = evaluate(
            [column for column in self.columns if column != "OBS_VALUE"],
            self.rows,
            now=datetime(2026, 8, 13, 17, 0, tzinfo=BERLIN),
        )
        self.assertEqual(report.contract_status, "fail")
        self.assertIn("schema.missing_columns", {item.code for item in report.findings})

    def test_identity_change_fails(self) -> None:
        rows = [dict(row) for row in self.rows]
        rows[0]["CURRENCY_DENOM"] = "GBP"
        report = evaluate(self.columns, rows, now=datetime(2026, 8, 13, 17, 0, tzinfo=BERLIN))
        self.assertIn("identity.changed", {item.code for item in report.findings})

    def test_duplicate_and_order_fail(self) -> None:
        rows = [dict(row) for row in self.rows]
        rows.append(dict(rows[-1]))
        rows[-1]["OBS_VALUE"] = "1.2"
        report = evaluate(self.columns, rows, now=datetime(2026, 8, 13, 17, 0, tzinfo=BERLIN))
        self.assertIn("data.duplicate_date", {item.code for item in report.findings})

        reversed_report = evaluate(
            self.columns,
            list(reversed(self.rows)),
            now=datetime(2026, 8, 13, 17, 0, tzinfo=BERLIN),
        )
        self.assertIn("data.out_of_order", {item.code for item in reversed_report.findings})

    def test_late_publication_fails_only_after_cutoff(self) -> None:
        before = evaluate(
            self.columns,
            self.rows,
            now=datetime(2026, 8, 14, 17, 59, tzinfo=BERLIN),
        )
        after = evaluate(
            self.columns,
            self.rows,
            now=datetime(2026, 8, 14, 18, 0, tzinfo=BERLIN),
        )
        self.assertNotIn("freshness.late", {item.code for item in before.findings})
        self.assertIn("freshness.late", {item.code for item in after.findings})

    def test_synthetic_extreme_is_review_not_failure(self) -> None:
        rows = []
        value = 1.0
        for offset in range(61):
            row = dict(self.rows[0])
            row["TIME_PERIOD"] = (
                date(2026, 1, 1).fromordinal(date(2026, 1, 1).toordinal() + offset).isoformat()
            )
            value *= math.exp(0.001 if offset % 2 else -0.001)
            row["OBS_VALUE"] = str(value)
            rows.append(row)
        rows[-1]["OBS_VALUE"] = str(float(rows[-2]["OBS_VALUE"]) * 1.2)
        report = evaluate(self.columns, rows, now=datetime(2026, 3, 2, 17, 0, tzinfo=BERLIN))
        self.assertEqual(report.contract_status, "pass")
        self.assertEqual(report.review_status, "review")

    def test_transport_failure_is_auditable_and_not_statistical(self) -> None:
        report = transport_failure(
            now=datetime(2026, 8, 13, 18, 0, tzinfo=BERLIN),
            error_type="TimeoutError",
        )
        self.assertEqual(report.contract_status, "fail")
        self.assertEqual(report.review_status, "not_evaluated")
        self.assertEqual(report.findings[0].code, "transport.unavailable")


class CalendarTests(unittest.TestCase):
    def test_easter_and_target_closings(self) -> None:
        self.assertEqual(easter_sunday(2026), date(2026, 4, 5))
        self.assertFalse(is_expected_publication_day(date(2026, 4, 3)))
        self.assertFalse(is_expected_publication_day(date(2026, 4, 6)))
        self.assertFalse(is_expected_publication_day(date(2026, 12, 25)))

    def test_latest_expected_day_skips_weekend_and_holiday(self) -> None:
        self.assertEqual(latest_expected_day(date(2026, 4, 6)), date(2026, 4, 2))


class EvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = FIXTURE.read_text(encoding="utf-8")
        self.columns, self.rows = parse_csv(self.text)

    def test_revision_comparison_covers_add_change_remove(self) -> None:
        previous = normalize(self.rows[:2])
        current_rows = [dict(row) for row in self.rows[1:3]]
        current_rows[0]["OBS_VALUE"] = "9.999"
        delta = compare(previous, normalize(current_rows))
        self.assertEqual(len(delta["added"]), 1)
        self.assertEqual(len(delta["changed"]), 1)
        self.assertEqual(len(delta["removed"]), 1)

    def test_ledger_is_append_only_and_indexes_runs(self) -> None:
        report = evaluate(
            self.columns,
            self.rows,
            now=datetime(2026, 8, 13, 17, 0, tzinfo=BERLIN),
        ).as_dict()
        with tempfile.TemporaryDirectory() as directory:
            run = record(self.text, report, Path(directory))
            index = json.loads((Path(directory) / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["prospective_run_count"], 1)
            self.assertEqual(run["delta"]["added"], sorted(normalize(self.rows)))
            with self.assertRaises(FileExistsError):
                record(self.text, report, Path(directory))

    def test_frozen_fault_manifest_classifies_every_case(self) -> None:
        manifest_path = Path(__file__).parents[1] / "evaluation/v1-fault-manifest.json"
        result = evaluate_suite(self.text, json.loads(manifest_path.read_text(encoding="utf-8")))
        self.assertEqual(result["detection_rate"], 1.0)
        self.assertEqual(result["controlled_false_alert_rate"], 0.0)
        self.assertTrue(all(case["matched"] for case in result["results"]))

    def test_replay_is_explicitly_not_revision_evidence(self) -> None:
        result = retrospective_replay(self.text)
        self.assertFalse(result["historical_revision_evidence"])


if __name__ == "__main__":
    unittest.main()
