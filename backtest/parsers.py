"""Parse Tech Titans CSV metric strings into numeric values."""

from __future__ import annotations


def parse_percent(value: str | None) -> float | None:
    """Convert values like ``10.7%`` or ``-5.9%`` to a decimal fraction."""
    if not value or value.strip() in {"", "—", "-", "N/A"}:
        return None
    text = value.strip().replace(",", "")
    if text.endswith("%"):
        text = text[:-1]
    try:
        return float(text) / 100.0
    except ValueError:
        return None


def parse_multiple(value: str | None) -> float | None:
    """Convert values like ``47.1x`` or ``3.4x`` to a float."""
    if not value or value.strip() in {"", "—", "-", "N/A"}:
        return None
    text = value.strip().replace(",", "").rstrip("xX")
    try:
        return float(text)
    except ValueError:
        return None


def parse_float(value: str | None) -> float | None:
    """Parse a plain numeric CSV field."""
    if not value or value.strip() in {"", "—", "-", "N/A"}:
        return None
    try:
        return float(value.strip().replace(",", ""))
    except ValueError:
        return None