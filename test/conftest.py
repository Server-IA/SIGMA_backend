import pytest


def pytest_configure():
    """Patch JWTAuthentication.authenticate early so tests don't depend on external tokens.

    This makes tests deterministic: the fake returns a JWTUser with permiso id 177 by default.
    """
    try:
        from users.authentication import JWTAuthentication, JWTUser

        _orig = getattr(JWTAuthentication, 'authenticate', None)

        def _fake_auth(self, request):
            payload = {
                "roles": [{
                    "permisos": [
                        {"id": 177},
                        {"id": 183},  # employee.list
                        {"id": 184},  # employee.employee_contract_list
                        {"id": 181},  # employee.employee_contract_detail
                    ]
                }],
                "id": 1000,
                "email": "test@example.com"
            }
            user = JWTUser(user_id=payload.get('id', 1000), email=payload.get('email'), name=None, raw_payload=payload)
            return (user, payload)

        JWTAuthentication.authenticate = _fake_auth
        pytest._orig_jwt_authenticate = _orig
    except Exception:
        # If anything fails, don't break the test collection phase
        pass


def pytest_unconfigure():
    try:
        orig = getattr(pytest, '_orig_jwt_authenticate', None)
        if orig is not None:
            from users.authentication import JWTAuthentication

            JWTAuthentication.authenticate = orig
    except Exception:
        pass
"""
Configuración global de pytest para todos los tests.

Este archivo contiene fixtures y configuraciones compartidas por todos los tests
del proyecto.
"""
import pytest
from django.utils import timezone
import os

# Ensure AUTH_SERVICE_URL is defined early for tests
os.environ.setdefault('AUTH_SERVICE_URL', 'http://auth-service')


@pytest.fixture(scope='session', autouse=True)
def patch_user_lookups_session():
    """Session fixture to stub external user lookups used by serializers.
    This ensures tests do not depend on network or env timing.
    """
    try:
        from monitoring.serializers.service_request_machinery_serializer import ServiceRequestMachineryDataSerializer
        from monitoring.serializers.data_serializer import DataSerializer

        orig_users = ServiceRequestMachineryDataSerializer._get_users_info
        orig_external = DataSerializer._get_external_user

        def _stub_get_users(self, ids):
            data = []
            for uid in ids or []:
                if int(uid) == 1:
                    data.append({'id': 1, 'name': 'Juan Andres', 'first_last_name': 'Veru', 'second_last_name': 'Sarmiento'})
                elif int(uid) == 2:
                    data.append({'id': 2, 'name': 'Juan', 'first_last_name': 'peralta petro', 'second_last_name': 'Sarmiento'})
            return data

        def _stub_external_user(self, user_id):
            users = _stub_get_users(None, [user_id])
            return users[0] if users else {}

        ServiceRequestMachineryDataSerializer._get_users_info = _stub_get_users
        DataSerializer._get_external_user = _stub_external_user
        yield
    finally:
        try:
            ServiceRequestMachineryDataSerializer._get_users_info = orig_users
            DataSerializer._get_external_user = orig_external
        except Exception:
            pass


def seed_ws_demo_data():
    """
    Seed minimal data to enable TelemetryProcessor processed flow for WS tests.
    
    Esta función crea:
    - Usuario de prueba
    - Estados necesarios (1, 20, 21)
    - Tipos y categorías
    - Marcas y modelos
    - Dispositivo telemetría con IMEI=357894561234567
    - Maquinaria vinculada al dispositivo
    - Cliente y solicitud de servicio activa
    - Ubicación y asignación de maquinaria
    
    Returns:
        dict: Diccionario con los objetos creados (user, device, machinery, customer, service_request)
    """
    from users.models import User
    from parameterization.models import (
        Statues, StatuesCategory, Types, TypesCategory,
        Brands, BrandsCategory, Models
    )
    from machinery.models import TelemetryDevices, Machinery
    from service_requests.models import (
        ServiceRequest, Customer, PersonType, TaxRegime,
        RequestLocation, RequestMachineryUser
    )

    now = timezone.now()

    # Users
    user, _ = User.objects.get_or_create(id_user=1)

    # Status categories and statuses
    sc, _ = StatuesCategory.objects.get_or_create(
        id_statues_categories=1,
        defaults=dict(
            name="General",
            description="Estados generales",
            modification_date=now,
            creation_date=now,
            id_responsible_user=user,
        ),
    )

    def ensure_status(pk: int, name: str):
        Statues.objects.get_or_create(
            id_statues=pk,
            defaults=dict(
                name=name,
                description=name,
                id_statues_categories=sc,
                modification_date=now,
                creation_date=now,
                id_responsible_user=user,
            ),
        )

    ensure_status(1, "Activo")
    ensure_status(20, "Solicitud Inicio (día de inicio)")
    ensure_status(21, "Solicitud Activa")
    ensure_status(22, "Finalizada")

    # Types
    tc, _ = TypesCategory.objects.get_or_create(
        id_types_categories=1,
        defaults=dict(
            name="Maquinaria",
            description="Tipos de maquinaria",
            creation_date=now,
            modification_date=now,
            id_responsible_user=user,
        ),
    )
    t_active = Statues.objects.get(id_statues=1)
    t1, _ = Types.objects.get_or_create(
        id_types=1,
        defaults=dict(
            name="TipoPrimario",
            description="",
            id_types_categories=tc,
            creation_date=now,
            modification_date=now,
            id_responsible_user=user,
            id_statues=t_active,
        ),
    )
    t2, _ = Types.objects.get_or_create(
        id_types=2,
        defaults=dict(
            name="TipoSecundario",
            description="",
            id_types_categories=tc,
            creation_date=now,
            modification_date=now,
            id_responsible_user=user,
            id_statues=t_active,
        ),
    )

    # Brands/Models (minimal)
    bc, _ = BrandsCategory.objects.get_or_create(
        id_brands_categories=1,
        defaults=dict(
            name="General",
            description="",
            modification_date=now,
            creation_date=now,
            id_responsible_user=user,
        ),
    )
    brand, _ = Brands.objects.get_or_create(
        id_brands=1,
        defaults=dict(
            name="DemoBrand",
            description="",
            id_brands_categories=bc,
            modification_date=now,
            creation_date=now,
            id_responsible_user=user,
            id_statues=t_active,
        ),
    )
    model, _ = Models.objects.get_or_create(
        id_model=1,
        defaults=dict(
            id_brand=brand,
            name="DemoModel",
            description="",
            modification_date=now,
            creation_date=now,
            id_responsible_user=user,
        ),
    )

    # Device
    imei = 357894561234567
    device, _ = TelemetryDevices.objects.get_or_create(
        IMEI=imei,
        defaults=dict(
            name="SIM Device",
            id_statues=t_active,
            id_responsible_user=user,
        ),
    )

    # Machinery
    machinery, _ = Machinery.objects.get_or_create(
        serial_number="SER1",
        defaults=dict(
            machinery_name="Demo Machine",
            manufacturing_year=2024,
            machinery_type=t1,
            id_model=model,
            tariff_subheading="",
            machinery_secondary_type=t2,
            id_country="CO",
            id_department="Cundinamarca",
            id_city=11001,
            image_path="",
            id_device=device,
            justification="test seed",
            machinery_operational_status=t_active,
            id_responsible_user=user,
        ),
    )
    # Ensure device link if machinery existed
    if machinery.id_device_id != device.id_device:
        machinery.id_device = device
        machinery.save(update_fields=["id_device"])

    # Customer dependencies
    pt, _ = PersonType.objects.get_or_create(name="Juridica")
    tr, _ = TaxRegime.objects.get_or_create(code="GEN", defaults=dict(name="General"))
    customer_status = t_active
    customer, _ = Customer.objects.get_or_create(
        legal_entity_name="Acme Corp",
        id_municipality=11001,
        tax_regime=tr,
        customer_statues=customer_status,
        id_responsible_user=user,
        defaults=dict(
            person_type=pt,
        ),
    )

    # Service request (active status 21, includes today)
    today = timezone.now().date()
    sr, _ = ServiceRequest.objects.get_or_create(
        id_request="REQ-WS-001",
        defaults=dict(
            customer=customer,
            request_detail="WS Demo Request",
            scheduled_start_date=today,
            scheduled_end_date=today,
            request_status=Statues.objects.get(id_statues=21),
            id_responsible_user=user,
        ),
    )

    # Location (optional but useful)
    RequestLocation.objects.get_or_create(
        request=sr,
        defaults=dict(
            country="CO",
            department="Cundinamarca",
            city_id=11001,
            place_name="Centro",
            latitude=4.60971,
            longitude=-74.08175,
        ),
    )

    # Link machinery to request
    RequestMachineryUser.objects.get_or_create(
        request=sr,
        machinery=machinery,
        user=user,
    )

    return {
        "user": user,
        "device": device,
        "machinery": machinery,
        "customer": customer,
        "service_request": sr,
    }


@pytest.fixture(scope="session")
def ws_demo_data(django_db_setup, django_db_blocker):
    """
    Fixture de sesión que crea datos de prueba para tests WebSocket.
    
    Uso:
        def test_something(ws_demo_data):
            # Los datos ya están en la BD
            assert ws_demo_data["device"].IMEI == 357894561234567
    """
    with django_db_blocker.unblock():
        return seed_ws_demo_data()
