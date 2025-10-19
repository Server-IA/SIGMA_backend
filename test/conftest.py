import json
import os
import pytest


# Configurar Django antes de importar cualquier cosa que dependa de settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "machpaymanager.settings")

if not os.environ.get("FIREBASE_CREDENTIALS"):
    fake_credentials = {
        "type": "service_account",
        "project_id": "local-test",
        "private_key_id": "dummy-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nFAKEKEY\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk@test.local",
        "client_id": "1234567890",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk@test.local",
        "universe_domain": "googleapis.com",
    }
    os.environ["FIREBASE_CREDENTIALS"] = json.dumps(fake_credentials).replace("\n", "\\\\n")

os.environ.setdefault("FIREBASE_STORAGE_BUCKET", "test-bucket.appspot.com")

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
    env_configured = False
    try:
        setup_test_environment()
        env_configured = True
    except RuntimeError:
        # Ya existe un entorno de prueba activo; reutilizarlo.
        env_configured = False

    for db_alias, db_config in settings.DATABASES.items():
        host = db_config.get("HOST")
        
        # Si está dentro de Docker (hay archivo /.dockerenv), usar 'db'; sino usar 'localhost'
        is_docker = os.path.isfile("/.dockerenv")
        
        if not host or host in {"db", "postgres", "postgres-db", "database"}:
            default_host = "db" if is_docker else "localhost"
            db_config["HOST"] = os.environ.get("PYTEST_DB_HOST", default_host)

        port_override = os.environ.get("PYTEST_DB_PORT")
        if port_override:
            db_config["PORT"] = port_override
        elif not db_config.get("PORT") or str(db_config.get("PORT")) == "5432":
            # En Docker el puerto es 5432, fuera es 5436
            db_config["PORT"] = "5432" if is_docker else "5436"

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    django_db_blocker = None
    try:
        django_db_blocker = request.getfixturevalue("django_db_blocker")
        django_db_blocker.unblock()
    except pytest.FixtureLookupError:
        django_db_blocker = None

    old_config = test_runner.setup_databases()

    def fin():
        test_runner.teardown_databases(old_config)
        if env_configured:
            teardown_test_environment()
        if django_db_blocker is not None:
            django_db_blocker.restore()

    request.addfinalizer(fin)
    return old_config
