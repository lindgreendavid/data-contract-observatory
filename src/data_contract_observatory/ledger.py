"""Create immutable evidence runs and a normalized revision-aware state."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from .ecb import parse_csv, source_identity

STATUS_FIELDS = ("OBS_STATUS", "OBS_CONF", "OBS_PRE_BREAK", "BREAKS")


def normalize(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """Index the evidence fields that define an observable revision."""
    return {
        row["TIME_PERIOD"]: {
            "value": row["OBS_VALUE"],
            **{field.lower(): row.get(field, "") for field in STATUS_FIELDS},
        }
        for row in rows
        if row.get("TIME_PERIOD") and row.get("OBS_VALUE")
    }


def compare(
    previous: dict[str, dict[str, str]], current: dict[str, dict[str, str]]
) -> dict[str, list[Any]]:
    previous_dates, current_dates = set(previous), set(current)
    changed = [
        {"date": key, "before": previous[key], "after": current[key]}
        for key in sorted(previous_dates & current_dates)
        if previous[key] != current[key]
    ]
    return {
        "added": sorted(current_dates - previous_dates),
        "changed": changed,
        "removed": sorted(previous_dates - current_dates),
    }


def record(csv_text: str, report: dict[str, object], evidence_dir: Path) -> dict[str, object]:
    columns, rows = parse_csv(csv_text)
    if not columns:
        raise ValueError("CSV has no header")
    current = normalize(rows)
    state_path = evidence_dir / "state.json"
    previous_payload = (
        json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    )
    previous = cast(dict[str, dict[str, str]], previous_payload.get("observations", {}))
    delta = compare(previous, current)
    checked_at = str(report["checked_at"])
    run_id = checked_at.replace(":", "-").replace("+", "_")
    source_hash = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
    run = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "checked_at": checked_at,
        "source_sha256": source_hash,
        "source": source_identity(),
        "contract_status": report["contract_status"],
        "review_status": report["review_status"],
        "observation_count": len(current),
        "latest_observation": max(current) if current else None,
        "delta": delta,
    }
    runs_dir = evidence_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_path = runs_dir / f"{run_id}.json"
    if run_path.exists():
        raise FileExistsError(f"immutable run already exists: {run_path}")
    run_path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    state = {
        "schema_version": "1.0.0",
        "updated_at": checked_at,
        "source_sha256": source_hash,
        "observations": current,
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    index_path = evidence_dir / "index.json"
    index: dict[str, Any] = (
        json.loads(index_path.read_text(encoding="utf-8"))
        if index_path.exists()
        else {"schema_version": "1.0.0", "runs": []}
    )
    index["runs"].append(
        {
            key: run[key]
            for key in (
                "run_id",
                "checked_at",
                "source_sha256",
                "contract_status",
                "review_status",
                "observation_count",
                "latest_observation",
                "delta",
            )
        }
    )
    index["run_count"] = len(index["runs"])
    index["prospective_run_count"] = len(index["runs"])
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    run = record(
        args.input.read_bytes().decode("utf-8"),
        json.loads(args.report.read_text(encoding="utf-8")),
        args.evidence_dir,
    )
    print(json.dumps(run, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
