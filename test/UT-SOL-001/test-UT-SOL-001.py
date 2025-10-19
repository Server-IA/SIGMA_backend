"""
Configuración de pytest para UT-SOL-001
Este archivo configura pytest-django para ejecutar correctamente
las pruebas dentro del contenedor Docker.
"""
import os
import pytest

# Configurar Django antes de cualquier importación
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "machpaymanager.settings")

# Configuración para ejecutar dentro de Docker
# La base de datos está en machpay_db:5432 (nombre del servicio en docker-compose)
os.environ["PYTEST_DB_HOST"] = "machpay_db"
os.environ["PYTEST_DB_PORT"] = "5432"

# Registro del marcador django_db
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "django_db: mark test to use django database"
    )
