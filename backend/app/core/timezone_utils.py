from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional, Union

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

DEFAULT_TIMEZONE_STR = "Asia/Kolkata"
IST_FALLBACK_TZ = timezone(timedelta(hours=5, minutes=30))


def get_timezone(tz_name: Optional[str] = None):
    """
    Returns a timezone object for the requested timezone name.
    Defaults to 'Asia/Kolkata' with rock-solid fallback.
    """
    name = tz_name or DEFAULT_TIMEZONE_STR
    if ZoneInfo:
        try:
            return ZoneInfo(name)
        except Exception:
            pass
    if name in ("Asia/Kolkata", "Asia/Calcutta", "IST"):
        return IST_FALLBACK_TZ
    return datetime.now().astimezone().tzinfo or timezone.utc


def now_utc() -> datetime:
    """Returns timezone-aware UTC datetime for the current real-world moment."""
    return datetime.now(timezone.utc)


def now_local(tz_name: Optional[str] = None) -> datetime:
    """Returns timezone-aware datetime in the user's local timezone (default Asia/Kolkata)."""
    tz = get_timezone(tz_name)
    return datetime.now(tz)


def today_local_date(tz_name: Optional[str] = None) -> date:
    """Returns the actual calendar date (year, month, day) in the local timezone."""
    return now_local(tz_name).date()


def today_local_str(tz_name: Optional[str] = None) -> str:
    """Returns the 'YYYY-MM-DD' calendar date string in the local timezone."""
    return today_local_date(tz_name).strftime("%Y-%m-%d")


def to_local_datetime(dt: Optional[datetime], tz_name: Optional[str] = None) -> Optional[datetime]:
    """Converts a UTC or naive datetime into the user's local timezone."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # DB naive timestamps are stored in UTC
        dt = dt.replace(tzinfo=timezone.utc)
    tz = get_timezone(tz_name)
    return dt.astimezone(tz)


def to_local_iso(dt: Optional[datetime], tz_name: Optional[str] = None) -> Optional[str]:
    """Converts datetime to ISO-8601 string in the local timezone."""
    local_dt = to_local_datetime(dt, tz_name)
    return local_dt.isoformat() if local_dt else None
