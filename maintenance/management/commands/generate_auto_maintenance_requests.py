import json
import logging

from django.core.management.base import BaseCommand

from maintenance.services.auto_maintenance_job import run_generate_auto_requests


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Genera solicitudes automáticas de mantenimiento basadas en programaciones periódicas "
        "y criterios de telemetría/inactividad conforme a la HU-SM-002."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra el resultado del job sin crear solicitudes en la base de datos.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        result = run_generate_auto_requests(dry_run=dry_run)

        self.stdout.write(self.style.SUCCESS(json.dumps(result)))
        logger.info("Job generate_auto_maintenance_requests ejecutado con resultado: %s", result)

