"""Timezone utility for application-layer date/hour calculations."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def get_local_now(tz_name: str) -> datetime:
    """Return the current datetime in the specified timezone.

    Args:
        tz_name: IANA timezone name (e.g. 'America/Sao_Paulo').

    Returns:
        Timezone-aware datetime in the given zone.
    """
    return datetime.now(ZoneInfo(tz_name))
