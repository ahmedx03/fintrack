"""
Management command: process_recurring
──────────────────────────────────────
Materialises due RecurringTransaction schedules into real Transaction rows
and advances each schedule's next_occurrence date.

Usage
─────
    python manage.py process_recurring            # process all due schedules
    python manage.py process_recurring --dry-run  # preview without writing

Deployment
──────────
Add a Render Cron Job that calls:
    python manage.py process_recurring
on a daily schedule (e.g. "0 0 * * *" — midnight UTC).
"""

import calendar
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from transactions.models import RecurringTransaction, Transaction


def _advance(date: datetime.date, interval: str) -> datetime.date:
    """Return the next occurrence date for a given interval."""
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


class Command(BaseCommand):
    help = 'Create transactions for all due recurring schedules.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview which transactions would be created without saving anything.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today   = datetime.date.today()

        due = (
            RecurringTransaction.objects
            .filter(is_active=True, next_occurrence__lte=today)
            .select_related('user', 'category')
        )

        if not due.exists():
            self.stdout.write('No recurring transactions are due.')
            return

        count = 0
        for rt in due:
            label = '[DRY RUN] Would create' if dry_run else 'Creating'
            self.stdout.write(
                f'  {label} {rt.type} ${rt.amount} for {rt.user} on {rt.next_occurrence}'
            )
            if not dry_run:
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

        suffix = ' (dry run — nothing written)' if dry_run else ''
        self.stdout.write(
            self.style.SUCCESS(f'Done — {count} schedule(s) processed.{suffix}')
        )
