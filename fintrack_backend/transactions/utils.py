"""
Shared utilities for the transactions and analytics apps.
"""
import calendar
import datetime

from django.db import transaction as db_transaction


def parse_date_param(value: str | None) -> datetime.date | None:
    """
    Safely parse an ISO date string from a query parameter.
    Returns None (silently ignores) if the value is missing or malformed.
    This prevents raw user input from reaching the ORM and avoids 500 errors
    on invalid query params.
    """
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _advance(date: datetime.date, interval: str) -> datetime.date:
    """Return the next occurrence date for a given interval."""
    # Avoid circular import — import inside function
    from transactions.models import RecurringTransaction

    if interval == RecurringTransaction.WEEKLY:
        return date + datetime.timedelta(weeks=1)

    # Monthly — same day next month, clamped to end-of-month
    month = date.month + 1
    year  = date.year
    if month > 12:
        month = 1
        year += 1
    last_day = calendar.monthrange(year, month)[1]
    return date.replace(year=year, month=month, day=min(date.day, last_day))


def process_recurring_for_user(user) -> int:
    """
    Materialise any due recurring transactions for a single user and advance
    each schedule's next_occurrence.

    Called lazily on GET /api/transactions/ so no cron job is needed — each
    user's schedules are processed the first time they open their transactions
    on or after the due date.

    Returns the number of transactions created.
    """
    from transactions.models import RecurringTransaction, Transaction

    today = datetime.date.today()
    due = (
        RecurringTransaction.objects
        .filter(user=user, is_active=True, next_occurrence__lte=today)
        .select_related('category')
    )

    count = 0
    for rt in due:
        with db_transaction.atomic():
            Transaction.objects.create(
                user=rt.user,
                category=rt.category,
                type=rt.type,
                amount=rt.amount,
                date=rt.next_occurrence,
                note=rt.note,
            )
            rt.next_occurrence = _advance(rt.next_occurrence, rt.interval)
            rt.save(update_fields=['next_occurrence'])
        count += 1

    return count
