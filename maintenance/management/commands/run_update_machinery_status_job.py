from django.core.management.base import BaseCommand
from maintenance.cron import update_machinery_status_job


class Command(BaseCommand):
    help = "Run the update_machinery_status_job once"

    def handle(self, *args, **options):
        update_machinery_status_job()
        self.stdout.write(self.style.SUCCESS("update_machinery_status_job executed"))
