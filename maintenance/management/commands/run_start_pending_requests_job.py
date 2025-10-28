from django.core.management.base import BaseCommand
from maintenance.cron import start_pending_requests_job


class Command(BaseCommand):
    help = "Run the start_pending_requests_job once"

    def handle(self, *args, **options):
        start_pending_requests_job()
        self.stdout.write(self.style.SUCCESS("start_pending_requests_job executed"))
