"""
Settings específicos para pruebas unitarias.
Utiliza SQLite en memoria para evitar dependencias de Docker.
"""
from machpaymanager.settings import *

# Sobrescribir configuración de base de datos para pruebas
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Deshabilitar migraciones para acelerar pruebas
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Configuración para pruebas
SECRET_KEY = 'test-secret-key-for-testing-only'
DEBUG = True

# Simplificar configuraciones que pueden causar problemas en pruebas
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}

# Deshabilitar servicios externos durante pruebas
AUTH_SERVICE_URL = 'http://localhost:8000'  # Mock URL