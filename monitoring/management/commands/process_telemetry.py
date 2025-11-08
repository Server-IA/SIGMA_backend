"""
Comando de Django para ejecutar el procesador de telemetría
Uso: python manage.py process_telemetry
"""
import logging
from django.core.management.base import BaseCommand
from monitoring.services.telemetry_processor import TelemetryProcessor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ejecuta el procesador de telemetría que escucha el WebSocket del simulador'

    def add_arguments(self, parser):
        parser.add_argument(
            '--simulator-url',
            type=str,
            default='ws://telemetry_simulator:8000/ws/telemetria',
            help='URL del WebSocket del simulador'
        )

    def handle(self, *args, **options):
        simulator_url = options['simulator_url']
        
        self.stdout.write(
            self.style.SUCCESS('Iniciando procesador de telemetria...')
        )
        self.stdout.write(f'URL del simulador: {simulator_url}')
        
        processor = TelemetryProcessor(simulator_url=simulator_url)
        
        try:
            processor.start()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nDeteniendo procesador...')
            )
            processor.stop()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            raise

