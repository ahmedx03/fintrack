"""
Shared utilities for the transactions and analytics apps.
"""
from datetime import date


def parse_date_param(value: str | None) -> date | None:
    """
    Safely parse an ISO date string from a query parameter.
    Returns None (silently ignores) if the value is missing or malformed.
    This prevents raw user input from reaching the ORM and avoids 500 errors
    on invalid query params.
    """
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None
