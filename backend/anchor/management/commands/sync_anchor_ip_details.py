from django.core.management.base import BaseCommand

from backend.anchor.sync import sync_anchor_ip

class Command(BaseCommand):

    help = "Sync UserAnchor → AnchorIpDetails with IPInfo enrichment"

    def handle(self, *args, **options):
        sync_anchor_ip()
