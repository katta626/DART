from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any
import re

from astropy import units as u


OBSERVATION_TIME_FORMAT = "%d_%m_%Y %H:%M:%S"
CLOCK_TIME_FORMAT = "%H:%M:%S"
LOG_DATE_FORMAT = "%d_%m_%Y"

_KNOWN_DATETIME_FORMATS = (
    OBSERVATION_TIME_FORMAT,
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
)
_TIME_PATTERN = re.compile(
    r"^(?P<hour>\d{1,2})(?P<separator>[:\-])(?P<minute>\d{2})(?:(?P=separator)(?P<second>\d{2}))?$"
)


def format_sidereal_time(angle: Any) -> str:
    """Return an astropy angle as a zero-padded clock string."""
    return angle.to_string(unit=u.hour, sep=":", precision=0, pad=True)


def normalize_observation_time(value: Any, *, reference: datetime | None = None) -> str:
    """Store every schedule time in one consistent string format."""
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.replace(microsecond=0).strftime(OBSERVATION_TIME_FORMAT)

    cleaned = str(value).strip()
    if not cleaned:
        return ""

    parsed_dt = _parse_datetime(cleaned)
    if parsed_dt is not None:
        return parsed_dt.replace(microsecond=0).strftime(OBSERVATION_TIME_FORMAT)

    parsed_time = _parse_clock(cleaned)
    if parsed_time is not None:
        base = (reference or datetime.now()).replace(microsecond=0)
        return datetime.combine(base.date(), parsed_time).strftime(OBSERVATION_TIME_FORMAT)

    return cleaned


def extract_clock_time(value: Any) -> str:
    """Extract a scheduler-friendly HH:MM:SS value from stored time strings."""
    if value is None:
        raise ValueError("Time value is empty.")

    if isinstance(value, datetime):
        return value.strftime(CLOCK_TIME_FORMAT)

    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError("Time value is empty.")

    parsed_dt = _parse_datetime(cleaned)
    if parsed_dt is not None:
        return parsed_dt.strftime(CLOCK_TIME_FORMAT)

    parsed_time = _parse_clock(cleaned)
    if parsed_time is not None:
        return parsed_time.strftime(CLOCK_TIME_FORMAT)

    raise ValueError("Use time values in HH:MM or HH:MM:SS format.")


def calculate_duration_minutes(start_value: Any, end_value: Any) -> int:
    """Return a positive duration in whole minutes, rounding up partial minutes."""
    start_clock = _parse_clock(extract_clock_time(start_value))
    end_clock = _parse_clock(extract_clock_time(end_value))

    if start_clock is None or end_clock is None:
        raise ValueError("Use time values in HH:MM or HH:MM:SS format.")

    today = datetime.now().date()
    start_dt = datetime.combine(today, start_clock)
    end_dt = datetime.combine(today, end_clock)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)

    duration_seconds = (end_dt - start_dt).total_seconds()
    return max(1, int((duration_seconds + 59) // 60))


def log_date_from_observation_time(value: Any) -> str:
    """Build the dd_mm_YYYY log date segment from a stored schedule time."""
    normalized = normalize_observation_time(value)
    parsed = _parse_datetime(normalized)
    if parsed is None:
        return datetime.now().strftime(LOG_DATE_FORMAT)
    return parsed.strftime(LOG_DATE_FORMAT)


def _parse_datetime(value: str) -> datetime | None:
    for time_format in _KNOWN_DATETIME_FORMATS:
        try:
            return datetime.strptime(value, time_format)
        except ValueError:
            continue
    return None


def _parse_clock(value: str) -> time | None:
    match = _TIME_PATTERN.fullmatch(value)
    if match is None:
        return None

    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second") or 0)

    try:
        return time(hour=hour, minute=minute, second=second)
    except ValueError:
        return None
