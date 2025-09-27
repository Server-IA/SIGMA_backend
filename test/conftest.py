import os
import pytest


# Configurar Django antes de importar cualquier cosa que dependa de settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "machpaymanager.settings")

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.test.utils import get_runner, setup_test_environment, teardown_test_environment  # noqa: E402

# Asegurar que Django quede configurado antes de que los tests importen DRF/APIClient
django.setup()


@pytest.fixture(scope="session", autouse=True)
def django_env_and_db(request):
    """
    Inicializa Django y crea la base de datos de pruebas usando el TestRunner de Django.
    Esto permite ejecutar pruebas con pytest sin depender de pytest-django.
    """
    setup_test_environment()

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    old_config = test_runner.setup_databases()

    def fin():
        test_runner.teardown_databases(old_config)
        teardown_test_environment()

    request.addfinalizer(fin)
    return old_config
