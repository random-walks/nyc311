"""CLI date parsing for the about-the-data example."""

from __future__ import annotations

from datetime import date, datetime, UTC


def parse_cli_date(raw: str | None) -> date:
    """Default end date: today (UTC) when ``raw`` is None."""
    if raw is None:
        return datetime.now(UTC).date()
    return date.fromisoformat(raw)
