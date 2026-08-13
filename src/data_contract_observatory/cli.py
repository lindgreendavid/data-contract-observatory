"""Command-line entry point for the observer."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .ecb import fetch_csv, parse_csv, source_identity, source_url
from .evaluate import evaluate, transport_failure


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Evaluate a saved ECB CSV instead of fetching.")
    parser.add_argument("--output", type=Path, help="Write the machine-readable report here.")
    parser.add_argument(
        "--raw-output", type=Path, help="Preserve the exact evaluated CSV response."
    )
    parser.add_argument(
        "--full-history", action="store_true", help="Fetch the complete current series."
    )
    args = parser.parse_args()

    now = datetime.now(ZoneInfo("Europe/Berlin"))
    try:
        text = (
            args.input.read_text(encoding="utf-8")
            if args.input
            else fetch_csv(lookback_days=None if args.full_history else 550)
        )
        columns, rows = parse_csv(text)
        report = evaluate(columns, rows, now=now)
    except (OSError, UnicodeError) as exc:
        report = transport_failure(now=now, error_type=type(exc).__name__)
    payload = report.as_dict()
    payload["source"] = source_identity()
    payload["query_url"] = source_url(lookback_days=None if args.full_history else 550)
    payload["source_sha256"] = (
        hashlib.sha256(text.encode("utf-8")).hexdigest() if "text" in locals() else None
    )
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if args.raw_output and "text" in locals():
        args.raw_output.parent.mkdir(parents=True, exist_ok=True)
        args.raw_output.write_text(text, encoding="utf-8")
    return 1 if report.contract_status == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
