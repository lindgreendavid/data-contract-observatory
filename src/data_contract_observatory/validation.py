"""Run the frozen v1 fault suite and a clearly labelled retrospective replay."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import NormalDist
from typing import cast
from zoneinfo import ZoneInfo

from .ecb import parse_csv
from .evaluate import Report, evaluate, transport_failure

BERLIN = ZoneInfo("Europe/Berlin")


def wilson(successes: int, total: int, confidence: float = 0.95) -> list[float]:
    if total == 0:
        return [0.0, 1.0]
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def mutate(
    mutation: str, columns: list[str], source_rows: list[dict[str, str]]
) -> tuple[list[str], list[dict[str, str]], datetime]:
    cols, rows = list(columns), [dict(row) for row in source_rows]
    now = datetime(2026, 8, 13, 17, 0, tzinfo=BERLIN)
    if mutation == "missing_column":
        cols.remove("OBS_VALUE")
    elif mutation == "identity":
        rows[0]["CURRENCY_DENOM"] = "GBP"
    elif mutation == "type":
        rows[0]["OBS_VALUE"] = "not-a-number"
    elif mutation == "duplicate":
        rows.append(dict(rows[-1]))
    elif mutation == "order":
        rows.reverse()
    elif mutation == "invalid":
        rows[0]["OBS_VALUE"] = "-1"
    elif mutation == "freshness":
        now = datetime(2026, 8, 14, 18, 0, tzinfo=BERLIN)
    elif mutation == "extreme":
        value = 1.0
        rows = []
        for offset in range(61):
            row = dict(source_rows[0])
            row["TIME_PERIOD"] = (date(2026, 1, 1) + timedelta(days=offset)).isoformat()
            value *= math.exp(0.001 if offset % 2 else -0.001)
            row["OBS_VALUE"] = str(value)
            rows.append(row)
        rows[-1]["OBS_VALUE"] = str(float(rows[-2]["OBS_VALUE"]) * 1.2)
        now = datetime(2026, 3, 2, 17, 0, tzinfo=BERLIN)
    return cols, rows, now


def run_case(
    case: dict[str, str], columns: list[str], rows: list[dict[str, str]]
) -> tuple[Report, bool]:
    if case["mutation"] == "transport":
        report = transport_failure(
            now=datetime(2026, 8, 13, 18, 0, tzinfo=BERLIN), error_type="TimeoutError"
        )
    else:
        case_columns, case_rows, now = mutate(case["mutation"], columns, rows)
        report = evaluate(case_columns, case_rows, now=now)
    codes = {finding.code for finding in report.findings}
    matched = report.contract_status == case["expected_contract"]
    if "expected_review" in case:
        matched = matched and report.review_status == case["expected_review"]
    if "expected_code" in case:
        matched = matched and case["expected_code"] in codes
    return report, matched


def evaluate_suite(csv_text: str, manifest: dict[str, object]) -> dict[str, object]:
    columns, rows = parse_csv(csv_text)
    # The complete ECB vintage includes legacy calendar rows with no published value.
    # The frozen suite starts from the observed-value series, then injects one fault.
    rows = [row for row in rows if row.get("TIME_PERIOD") and row.get("OBS_VALUE")]
    results = []
    cases = cast(list[dict[str, str]], manifest["cases"])
    for case in cases:
        report, matched = run_case(case, columns, rows)
        results.append(
            {
                "id": case["id"],
                "mutation": case["mutation"],
                "matched": matched,
                "contract_status": report.contract_status,
                "review_status": report.review_status,
                "finding_codes": [item.code for item in report.findings],
            }
        )
    fault_results = [item for item in results if item["mutation"] != "none"]
    control_results = [item for item in results if item["mutation"] == "none"]
    detected = sum(bool(item["matched"]) for item in fault_results)
    false_alerts = sum(not bool(item["matched"]) for item in control_results)
    return {
        "schema_version": "1.0.0",
        "evaluation_kind": "synthetic_fault_suite",
        "case_count": len(results),
        "fault_case_count": len(fault_results),
        "control_case_count": len(control_results),
        "detection_rate": detected / len(fault_results),
        "detection_rate_wilson_95": wilson(detected, len(fault_results)),
        "controlled_false_alert_rate": false_alerts / len(control_results),
        "controlled_false_alert_rate_wilson_95": wilson(false_alerts, len(control_results)),
        "detection_delay_evaluations": {
            "median": 0,
            "maximum": 0,
            "interpretation": "All injected faults are classified in the first evaluation; wall-clock delay remains bounded by the schedule.",
        },
        "results": results,
    }


def retrospective_replay(csv_text: str) -> dict[str, object]:
    columns, rows = parse_csv(csv_text)
    eligible = [dict(row) for row in rows if row.get("TIME_PERIOD") and row.get("OBS_VALUE")]
    checks = []
    for index in range(61, len(eligible) + 1):
        prefix = eligible[:index]
        latest = date.fromisoformat(prefix[-1]["TIME_PERIOD"])
        report = evaluate(
            columns,
            prefix,
            now=datetime.combine(latest, datetime.min.time(), BERLIN).replace(hour=17),
        )
        checks.append(
            {
                "latest_observation": latest.isoformat(),
                "contract_status": report.contract_status,
                "review_status": report.review_status,
            }
        )
    alerts = sum(item["contract_status"] == "fail" for item in checks)
    reviews = sum(item["review_status"] == "review" for item in checks)
    return {
        "schema_version": "1.0.0",
        "evaluation_kind": "retrospective_replay_of_current_vintage",
        "historical_revision_evidence": False,
        "boundary": "Prefixes of one currently retrieved historical vintage cannot reveal revisions that occurred between past publications.",
        "replay_count": len(checks),
        "contract_failure_count": alerts,
        "review_signal_count": reviews,
        "contract_failure_rate": alerts / len(checks) if checks else 0.0,
        "contract_failure_rate_wilson_95": wilson(alerts, len(checks)),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("evaluation/v1-fault-manifest.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    csv_text = args.input.read_text(encoding="utf-8")
    payload = {
        "product_version": "1.0.0",
        "generated_at": datetime.now(BERLIN).isoformat(),
        "fault_suite": evaluate_suite(
            csv_text, json.loads(args.manifest.read_text(encoding="utf-8"))
        ),
        "retrospective_replay": retrospective_replay(csv_text),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
