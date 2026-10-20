"""Generate the post-hoc review-threshold audit from the checksummed ECB snapshot."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from data_contract_observatory.ecb import parse_csv
from data_contract_observatory.threshold_audit import build_threshold_audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("data/ecb-exr-usd-eur-to-2026-08-13.csv")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("reports/post-release-threshold-audit.json")
    )
    args = parser.parse_args()
    _, rows = parse_csv(args.input.read_text(encoding="utf-8-sig"))
    eligible = [row for row in rows if row.get("TIME_PERIOD") and row.get("OBS_VALUE")]
    dates = [date.fromisoformat(row["TIME_PERIOD"]) for row in eligible]
    values = [float(row["OBS_VALUE"]) for row in eligible]
    payload = build_threshold_audit(dates, values)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
