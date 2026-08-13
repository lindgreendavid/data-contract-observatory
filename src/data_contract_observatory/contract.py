"""The frozen ECB series contract and TARGET operating-day calendar."""

from __future__ import annotations

from datetime import date, timedelta

SERIES_KEY = "EXR.D.USD.EUR.SP00.A"

REQUIRED_COLUMNS = (
    "KEY",
    "FREQ",
    "CURRENCY",
    "CURRENCY_DENOM",
    "EXR_TYPE",
    "EXR_SUFFIX",
    "TIME_PERIOD",
    "OBS_VALUE",
    "OBS_STATUS",
    "OBS_CONF",
    "TIME_FORMAT",
    "COLLECTION",
    "DECIMALS",
    "SOURCE_AGENCY",
    "TITLE",
    "TITLE_COMPL",
    "UNIT",
    "UNIT_MULT",
)

IDENTITY = {
    "KEY": SERIES_KEY,
    "FREQ": "D",
    "CURRENCY": "USD",
    "CURRENCY_DENOM": "EUR",
    "EXR_TYPE": "SP00",
    "EXR_SUFFIX": "A",
    "TIME_FORMAT": "P1D",
    "COLLECTION": "A",
    "SOURCE_AGENCY": "4F0",
    "UNIT": "USD",
    "UNIT_MULT": "0",
}


def easter_sunday(year: int) -> date:
    """Return Gregorian Easter Sunday using the Meeus/Jones/Butcher algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def target_closing_days(year: int) -> frozenset[date]:
    """Return the published recurring TARGET closing days for a year."""
    easter = easter_sunday(year)
    return frozenset(
        {
            date(year, 1, 1),
            easter - timedelta(days=2),
            easter + timedelta(days=1),
            date(year, 5, 1),
            date(year, 12, 25),
            date(year, 12, 26),
        }
    )


def is_expected_publication_day(day: date) -> bool:
    return day.weekday() < 5 and day not in target_closing_days(day.year)


def latest_expected_day(day: date) -> date:
    candidate = day
    while not is_expected_publication_day(candidate):
        candidate -= timedelta(days=1)
    return candidate
