from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from backend.anchor.measurement import update_measurement_public
from django.utils import timezone


class Command(BaseCommand):
    help = "Bulk update is_public=True for given users and date range"

    def add_arguments(self, parser):
        parser.add_argument(
            '--user_ids',
            type=str,
            required=True,
            help="Comma separated user IDs (e.g. 1,2,3)"
        )
        parser.add_argument(
            '--start_date',
            type=str,
            required=True,
            help="Start datetime (e.g. 2026-01-01T00:00:00)"
        )
        parser.add_argument(
            '--end_date',
            type=str,
            required=False,
            help="Optional end datetime"
        )
        parser.add_argument(
            '--is_public',
            type=str,
            required=False,
            default="true",
            help="Set true or false (default: true)"
        )

    def handle(self, *args, **kwargs):
        try:
            # Parse user_ids
            user_ids = [
                int(uid.strip()) for uid in kwargs['user_ids'].split(',')
                if uid.strip()
            ]

            if not user_ids:
                self.stdout.write(self.style.ERROR("[ERROR] No valid user IDs provided"))
                return

            # Parse dates
            start_date = parse_datetime(kwargs['start_date'])
            end_date = parse_datetime(kwargs.get('end_date')) if kwargs.get('end_date') else None

            if not start_date:
                self.stdout.write(self.style.ERROR("[ERROR] Invalid start_date format"))
                return

            if end_date and not end_date:
                self.stdout.write(self.style.ERROR("[ERROR] Invalid end_date format"))
                return

            # Make timezone aware
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)

            if end_date and timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)

            is_public_input = kwargs.get("is_public", "true").lower()
            
            if is_public_input not in ["true", "false"]:
                self.stdout.write(self.style.ERROR("[ERROR] is_public must be true or false"))
                return
            is_public = True if is_public_input == "true" else False

            # Call reusable function
            updated = update_measurement_public(user_ids, start_date, end_date, is_public)

            self.stdout.write(self.style.SUCCESS(
                f"[DONE] Total updated: {updated}"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] {str(e)}"))
