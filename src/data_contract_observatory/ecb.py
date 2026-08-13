"""Fetch and parse the pinned ECB SDMX CSV representation."""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .contract import SERIES_KEY

API_ROOT = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"


def source_url(*, end: date | None = None, lookback_days: int = 550) -> str:
    end = end or date.today()
    query = urlencode(
        {
            "startPeriod": (end - timedelta(days=lookback_days)).isoformat(),
            "endPeriod": end.isoformat(),
            "detail": "full",
        }
    )
    return f"{API_ROOT}?{query}"


def fetch_csv(*, end: date | None = None, timeout: int = 30) -> str:
    request = Request(
        source_url(end=end),
        headers={"Accept": "text/csv", "User-Agent": "data-contract-observatory/0.1"},
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - pinned HTTPS host
        return response.read().decode("utf-8-sig")


def parse_csv(text: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return [], []
    return list(reader.fieldnames), [dict(row) for row in reader]


def source_identity() -> dict[str, str]:
    return {"provider": "European Central Bank", "series_key": SERIES_KEY, "url": API_ROOT}

