"""Lightweight display helpers for example scripts and notebooks."""

from __future__ import annotations

from collections.abc import Iterable, Sequence


def print_section(title: str) -> None:
    """Print a simple section header."""
    print(title)
    print("-" * len(title))


def print_counter(
    title: str,
    rows: Iterable[tuple[str, int]],
    *,
    limit: int = 5,
) -> None:
    """Print the top rows from a counter-style iterable."""
    print(title)
    for label, count in list(rows)[:limit]:
        print(f"  {label}: {count}")


def print_lines(title: str, lines: Sequence[str]) -> None:
    """Print a titled sequence of lines."""
    print(title)
    for line in lines:
        print(f"  {line}")
