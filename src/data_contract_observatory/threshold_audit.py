"""POST-HOC (not preregistered): how often would other review thresholds fire on the real series?

The frozen v1 evaluation reports 9 review signals in 7,010 replayed prefixes at the preregistered
threshold (absolute robust z-score >= 6). It does not say how that count depends on the threshold
or how it compares with what a Gaussian return model would predict. This module recomputes the
robust z-score of every replayed day (same baseline: the preceding 250 log returns) and reports,
for several thresholds, the empirical number of signals, the Gaussian expectation, and how many
distinct episodes the signals form. Standard library only.
"""

from __future__ import annotations

import math
import statistics
from datetime import date
from itertools import pairwise

THRESHOLDS = (3.0, 4.0, 5.0, 6.0, 8.0)
MIN_VALUES = 61
BASELINE = 250
EPISODE_GAP_DAYS = 5


def robust_scores(dates: list[date], values: list[float]) -> list[tuple[date, float]]:
    """Robust z-score of each day's log return against its preceding baseline."""

    returns = [math.log(current / previous) for previous, current in pairwise(values)]
    scores: list[tuple[date, float]] = []
    for end in range(MIN_VALUES, len(values) + 1):
        window = returns[: end - 1]
        latest = window[-1]
        baseline = window[-(BASELINE + 1) : -1]
        median = statistics.median(baseline)
        mad = statistics.median(abs(value - median) for value in baseline)
        if mad == 0:
            score = math.inf if latest != median else 0.0
        else:
            score = (latest - median) / (1.4826 * mad)
        scores.append((dates[end - 1], score))
    return scores


def gaussian_two_sided(threshold: float) -> float:
    return math.erfc(threshold / math.sqrt(2.0))


def episodes(flagged: list[date]) -> int:
    count = 0
    previous: date | None = None
    for day in flagged:
        if previous is None or (day - previous).days > EPISODE_GAP_DAYS:
            count += 1
        previous = day
    return count


def build_threshold_audit(dates: list[date], values: list[float]) -> dict[str, object]:
    scores = robust_scores(dates, values)
    total = len(scores)
    rows = []
    for threshold in THRESHOLDS:
        flagged = [day for day, score in scores if abs(score) >= threshold]
        expected_rate = gaussian_two_sided(threshold)
        rows.append(
            {
                "threshold": threshold,
                "signals": len(flagged),
                "rate": len(flagged) / total,
                "gaussian_expected_signals": expected_rate * total,
                "episodes": episodes(flagged),
                "dates": [day.isoformat() for day in flagged] if len(flagged) <= 40 else [],
            }
        )
    return {
        "schema_version": 1,
        "label": "POST-HOC (not preregistered): review-threshold sensitivity on the real series",
        "evaluated_days": total,
        "infinite_scores": sum(math.isinf(score) for _, score in scores),
        "episode_gap_days": EPISODE_GAP_DAYS,
        "thresholds": rows,
    }
