from django.core.management.base import BaseCommand

from backend.anchor.sync import sync_pending_measurements

class Command(BaseCommand):

    help = "Sync pending measurements data"

    def handle(self, *args, **options):
        sync_pending_measurements()
