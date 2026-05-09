"""
Management command: process_recurring
──────────────────────────────────────
Materialises due RecurringTransaction schedules into real Transaction rows
and advances each schedule's next_occurrence date.

NOTE: In production this command is no longer required as a cron job.
Recurring transactions are processed lazily per-user on GET /api/transactions/.
This command remains useful for manual runs, backfills, or admin tooling.

Usage
─────
    python manage.py process_recurring            # process all due schedules
    python manage.py process_recurring --dry-run  # preview without writing
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from transactions.utils import process_recurring_for_user

User = get_user_model()


class Command(BaseCommand):
    help = 'Create transactions for all due recurring schedules (all users).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview how many transactions would be created without saving anything.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today   = datetime.date.today()

        from transactions.models import RecurringTransaction
        due_user_ids = (
            RecurringTransaction.objects
            .filter(is_active=True, next_occurrence__lte=today)
            .values_list('user_id', flat=True)
            .distinct()
        )

        if not due_user_ids:
            self.stdout.write('No recurring transactions are due.')
            return

        if dry_run:
            count = RecurringTransaction.objects.filter(
                is_active=True, next_occurrence__lte=today
            ).count()
            self.stdout.write(f'[DRY RUN] Would process {count} schedule(s) across {len(due_user_ids)} user(s).')
            return

        total = 0
        for user in User.objects.filter(id__in=due_user_ids):
            created = process_recurring_for_user(user)
            self.stdout.write(f'  {user.username}: {created} transaction(s) created.')
            total += created

        self.stdout.write(self.style.SUCCESS(f'Done — {total} transaction(s) created in total.'))
