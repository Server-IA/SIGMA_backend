from django.core.management.base import BaseCommand
from service_requests.cron import sync_customers_users_job


class Command(BaseCommand):
    help = "Run the sync_customers_users_job once"

    def handle(self, *args, **options):
        sync_customers_users_job()
        self.stdout.write(self.style.SUCCESS("sync_customers_users_job executed"))


