"""Evaluate contract failures separately from statistical review signals."""

from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from .contract import IDENTITY, REQUIRED_COLUMNS, latest_expected_day


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class Report:
    checked_at: str
    contract_status: str
    review_status: str
    observation_count: int
    latest_observation: str | None
    findings: tuple[Finding, ...]

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["method"] = {
            "contract": "exact schema, identity, type, uniqueness, ordering and freshness checks",
            "review_signal": "absolute robust z-score >= 6 on the latest log return; 250-day baseline",
        }
        return result


def transport_failure(*, now: datetime, error_type: str) -> Report:
    """Represent an unavailable source as an auditable contract failure."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    local_now = now.astimezone(ZoneInfo("Europe/Berlin"))
    return Report(
        checked_at=local_now.isoformat(),
        contract_status="fail",
        review_status="not_evaluated",
        observation_count=0,
        latest_observation=None,
        findings=(
            Finding(
                code="transport.unavailable",
                severity="failure",
                message=f"The pinned source could not be evaluated ({error_type}).",
            ),
        ),
    )


def _finding(code: str, severity: str, message: str) -> Finding:
    return Finding(code=code, severity=severity, message=message)


def _robust_latest_return(values: list[float]) -> float | None:
    if len(values) < 61 or any(value <= 0 for value in values):
        return None
    returns = [math.log(current / previous) for previous, current in zip(values, values[1:])]
    latest = returns[-1]
    baseline = returns[-251:-1]
    median = statistics.median(baseline)
    mad = statistics.median(abs(value - median) for value in baseline)
    if mad == 0:
        return math.inf if latest != median else 0.0
    return (latest - median) / (1.4826 * mad)


def evaluate(
    columns: list[str],
    rows: list[dict[str, str]],
    *,
    now: datetime | None = None,
) -> Report:
    now = now or datetime.now(ZoneInfo("Europe/Berlin"))
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    local_now = now.astimezone(ZoneInfo("Europe/Berlin"))
    findings: list[Finding] = []

    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        findings.append(_finding("schema.missing_columns", "failure", ", ".join(missing)))
    if not rows:
        findings.append(_finding("data.empty", "failure", "The response contains no observations."))

    dates: list[date] = []
    values: list[float] = []
    seen: set[date] = set()
    for index, row in enumerate(rows, start=1):
        for field, expected in IDENTITY.items():
            if field in columns and row.get(field) != expected:
                findings.append(
                    _finding(
                        "identity.changed",
                        "failure",
                        f"Row {index}: {field}={row.get(field)!r}, expected {expected!r}.",
                    )
                )
        try:
            observed = date.fromisoformat(row["TIME_PERIOD"])
            value = float(row["OBS_VALUE"])
            if not math.isfinite(value) or value <= 0:
                raise ValueError("value must be finite and positive")
        except (KeyError, TypeError, ValueError) as exc:
            findings.append(_finding("data.invalid_value", "failure", f"Row {index}: {exc}"))
            continue
        if observed in seen:
            findings.append(_finding("data.duplicate_date", "failure", observed.isoformat()))
        seen.add(observed)
        dates.append(observed)
        values.append(value)

    if dates and dates != sorted(dates):
        findings.append(_finding("data.out_of_order", "failure", "Observation dates are not ascending."))

    latest = max(dates) if dates else None
    publish_cutoff = time(18, 0)
    if latest and local_now.time() >= publish_cutoff:
        expected = latest_expected_day(local_now.date())
        if latest < expected:
            findings.append(
                _finding(
                    "freshness.late",
                    "failure",
                    f"Latest observation is {latest}; expected {expected} after the 18:00 CET/CEST grace period.",
                )
            )

    robust_z = _robust_latest_return(values)
    if robust_z is not None and abs(robust_z) >= 6:
        findings.append(
            _finding(
                "distribution.extreme_latest_return",
                "review",
                f"Latest log return has robust z={robust_z:.2f}; inspect, but do not infer a source error.",
            )
        )

    contract_status = "fail" if any(item.severity == "failure" for item in findings) else "pass"
    review_status = "review" if any(item.severity == "review" for item in findings) else "clear"
    return Report(
        checked_at=local_now.isoformat(),
        contract_status=contract_status,
        review_status=review_status,
        observation_count=len(rows),
        latest_observation=latest.isoformat() if latest else None,
        findings=tuple(findings),
    )
