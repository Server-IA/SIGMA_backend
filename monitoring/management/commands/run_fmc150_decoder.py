"""
Comando de Django para ejecutar el servidor decodificador FMC150
Uso: python manage.py run_fmc150_decoder
"""
import logging
from django.core.management.base import BaseCommand
from fmc150_decoder.server import FMC150Server

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Ejecuta el servidor decodificador FMC150 que recibe datos del dispositivo y los envía al simulador'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='0.0.0.0',
            help='Host para escuchar conexiones (default: 0.0.0.0)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=5055,
            help='Puerto para escuchar conexiones (default: 5055)'
        )
        parser.add_argument(
            '--simulator-url',
            type=str,
            default='http://telemetry_simulator:8000',
            help='URL del simulador de telemetría'
        )

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        simulator_url = options['simulator_url']
        
        # Configurar variables de entorno
        import os
        os.environ['FMC150_HOST'] = host
        os.environ['FMC150_PORT'] = str(port)
        os.environ['SIMULATOR_URL'] = simulator_url
        
        self.stdout.write(
            self.style.SUCCESS('Iniciando servidor decodificador FMC150...')
        )
        self.stdout.write(f'Host: {host}')
        self.stdout.write(f'Puerto: {port}')
        self.stdout.write(f'Simulador: {simulator_url}')
        
        server = FMC150Server()
        
        try:
            server.run()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nDeteniendo servidor...')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            raise

