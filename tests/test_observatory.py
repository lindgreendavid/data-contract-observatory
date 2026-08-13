from __future__ import annotations

import math
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
            row["TIME_PERIOD"] = date(2026, 1, 1).fromordinal(date(2026, 1, 1).toordinal() + offset).isoformat()
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


if __name__ == "__main__":
    unittest.main()
