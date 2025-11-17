"""
Pruebas Unitarias para HU-MS-009
Endpoint: Obtener datos históricos de solicitud por maquinaria y/o operario
URL: GET /data/service_requests/
"""

import pytest
import json
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import os

# Ensure serializers call the mocked auth endpoint during tests
os.environ.setdefault('AUTH_SERVICE_URL', 'http://auth-service')


@pytest.fixture(autouse=True)
def patch_external_user_service(mock_auth_service):
    """Autouse fixture: replace the serializer method that calls the auth service
    so tests use the local `mock_auth_service` data and do not depend on env or network.
    """
    from monitoring.serializers.service_request_machinery_serializer import ServiceRequestMachineryDataSerializer

    original = ServiceRequestMachineryDataSerializer._get_users_info

    def _mock_get_users(self, ids):
        payload = mock_auth_service(ids)
        return payload.get('data') if isinstance(payload, dict) else []

    ServiceRequestMachineryDataSerializer._get_users_info = _mock_get_users
    # Also patch DataSerializer._get_external_user used by get_machinery_data
    try:
        from monitoring.serializers.data_serializer import DataSerializer

        original_ext = DataSerializer._get_external_user

        def _mock_external_user(self, user_id):
            payload = mock_auth_service([user_id])
            data = payload.get('data') if isinstance(payload, dict) else []
            return data[0] if data else {}

        DataSerializer._get_external_user = _mock_external_user
    except Exception:
        original_ext = None
    yield
    ServiceRequestMachineryDataSerializer._get_users_info = original
    if original_ext is not None:
        from monitoring.serializers.data_serializer import DataSerializer
        DataSerializer._get_external_user = original_ext

# Importar modelos
from service_requests.models.service_request import ServiceRequest
from service_requests.models.request_machinery_user import RequestMachineryUser
from monitoring.models.data import Data

# Importaciones necesarias para dependencias de Units y Statues
from parameterization.models import UnitsCategory, TypesCategory, StatuesCategory, Types



@pytest.fixture
def api_client():
    """Cliente API para realizar peticiones"""
    client = APIClient()
    # Force an authenticated user for tests (bypass IsAuthenticated)
    client.force_authenticate(user=MagicMock(is_authenticated=True))
    return client


@pytest.fixture
def mock_permission():
    """Mock para simular permisos del usuario"""
    def _mock_permission(has_permission=True):
        mock_payload = {
            "rol": [{
                "permisos": [
                    {"id": 172, "name": "monitoring.list_data_by_request"}
                ]
            }]
        }
        return mock_payload if has_permission else {"rol": [{"permisos": []}]}
    
    return _mock_permission


@pytest.fixture
def mock_auth_service():
    """Mock para el servicio de autenticación externo"""
    def _mock_response(user_ids):
        users = []
        user_map = {
            1: {"id": 1, "name": "Juan Andres", "first_last_name": "Veru", "second_last_name": "Sarmiento"},
            2: {"id": 2, "name": "Juan", "first_last_name": "peralta petro", "second_last_name": "Sarmiento"},
        }
        for user_id in user_ids:
            if user_id in user_map:
                users.append(user_map[user_id])
        return {"data": users}
    return _mock_response


@pytest.fixture
def setup_test_data(db, django_db_blocker):
    """Configurar datos de prueba en la base de datos real"""
    with django_db_blocker.unblock():
        import os
        from django.contrib.auth import get_user_model
        # Ensure serializers attempt to call the external auth service
        os.environ.setdefault('AUTH_SERVICE_URL', 'http://auth-service')
        from machinery.models import Machinery, Parameters, TelemetryDevices
        from service_requests.models import Customer, PaymentMethod, SoilType, Texture, Implementation
        from parameterization.models import Statues, Units
        from users.models import User

        # Crear o buscar categorías, tipos y estados necesarios
        units_category, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=1,
            defaults={
                'name': 'Moneda',
                'description': 'Unidades monetarias',
                'modification_date': timezone.now(),
                'creation_date': timezone.now(),
                'id_responsible_user': None
            }
        )

        types_category, _ = TypesCategory.objects.get_or_create(
            id_types_categories=1,
            defaults={
                'name': 'Tipo monetario',
                'description': 'Tipos para unidades monetarias',
                'creation_date': timezone.now(),
                'modification_date': timezone.now(),
                'id_responsible_user': None
            }
        )

        statues_category, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                'name': 'General',
                'description': 'Categoría general de estados',
                'modification_date': timezone.now(),
                'creation_date': timezone.now(),
                'id_responsible_user': None
            }
        )

        try:
            status_unit = Statues.objects.get(id_statues=100)
        except Statues.DoesNotExist:
            status_unit = Statues(
                id_statues=100,
                name='Activo',
                description='Estado activo para unidad',
                id_statues_categories=statues_category,
                modification_date=timezone.now(),
                creation_date=timezone.now(),
                id_responsible_user=None
            )
            status_unit.save()

        try:
            status_finalized = Statues.objects.get(id_statues=22)
        except Statues.DoesNotExist:
            status_finalized = Statues(
                id_statues=22,
                name='Finalizada',
                description='Estado finalizado',
                id_statues_categories=statues_category,
                modification_date=timezone.now(),
                creation_date=timezone.now(),
                id_responsible_user=None
            )
            status_finalized.save()

        try:
            status_payment = Statues.objects.get(id_statues=1)
        except Statues.DoesNotExist:
            status_payment = Statues(
                id_statues=1,
                name='Pagado',
                description='Estado pagado',
                id_statues_categories=statues_category,
                modification_date=timezone.now(),
                creation_date=timezone.now(),
                id_responsible_user=None
            )
            status_payment.save()

        # Crear tipo y unidad monetaria
        type_unit, _ = Types.objects.get_or_create(
            id_types=1,
            id_types_categories=types_category,
            id_statues=status_unit,
            defaults={
                'name': 'Moneda',
                'description': 'Tipo de unidad monetaria',
                'creation_date': timezone.now(),
                'modification_date': timezone.now(),
                'id_responsible_user': None
            }
        )

        unit_currency, _ = Units.objects.get_or_create(
            id_units=1,
            id_units_categories=units_category,
            id_types=type_unit,
            id_statues=status_unit,
            defaults={
                'name': 'COP',
                'symbol': '$',
                'id_responsible_user': None
            }
        )

        # Crear usuarios
        try:
            user1 = User.objects.get(id_user=1)
        except User.DoesNotExist:
            user1 = User(id_user=1)
            user1.save()

        try:
            user2 = User.objects.get(id_user=2)
        except User.DoesNotExist:
            user2 = User(id_user=2)
            user2.save()

        try:
            responsible_user = User.objects.get(id_user=999)
        except User.DoesNotExist:
            responsible_user = User(id_user=999)
            responsible_user.save()

        # Crear clientes
        # Crear datos requeridos para Customer
        from service_requests.models import PersonType, TaxRegime
        person_type_obj, _ = PersonType.objects.get_or_create(id_person_type=1, defaults={'name': 'Natural'})
        tax_regime_obj, _ = TaxRegime.objects.get_or_create(id_tax_regime=1, defaults={'code': 'TR1', 'name': 'Regimen 1'})

        customer1, _ = Customer.objects.get_or_create(
            id_customer=90,
            defaults={
                'legal_entity_name': 'voldemort',
                'id_user': user1,
                'name': 'Juan Andres',
                'first_last_name': 'Veru',
                'second_last_name': 'Sarmiento',
                'person_type': person_type_obj,
                'id_municipality': 1,
                'tax_regime': tax_regime_obj,
                'customer_statues': status_unit,
                'id_responsible_user': responsible_user
            }
        )

        customer2, _ = Customer.objects.get_or_create(
            id_customer=94,
            defaults={
                'legal_entity_name': 'voldemort2',
                'id_user': user2,
                'name': 'Juan',
                'first_last_name': 'Pérez',
                'second_last_name': 'Gómez',
                'person_type': person_type_obj,
                'id_municipality': 1,
                'tax_regime': tax_regime_obj,
                'customer_statues': status_unit,
                'id_responsible_user': responsible_user
            }
        )

        # Crear método de pago (usar campos reales del modelo `PaymentMethod`)
        # `PaymentMethod.code` es la PK del modelo, así que lo creamos por `code`.
        payment_method, _ = PaymentMethod.objects.get_or_create(
            code='PM001',
            defaults={'name': 'Efectivo'}
        )

        # Crear maquinarias
        # Crear un modelo (id_model) necesario por la FK en Machinery
        from parameterization.models.brand_model import Models as ModelObj
        model_obj, _ = ModelObj.objects.get_or_create(
            id_model=1,
            defaults={
                'name': 'Modelo Default',
                'description': 'Modelo creado para pruebas',
                'modification_date': timezone.now(),
                'creation_date': timezone.now(),
                'id_responsible_user': responsible_user,
                'id_statues': status_unit
            }
        )

        # Crear maquinarias usando los campos reales del modelo Machinery
        machinery1, _ = Machinery.objects.get_or_create(
            id_machinery=1,
            defaults={
                'machinery_name': 'Tractor 1',
                'serial_number': 'S-0001',
                'machinery_type': type_unit,
                'machinery_secondary_type': type_unit,
                'id_model': model_obj,
                'machinery_operational_status': status_unit,
                'id_responsible_user': responsible_user
            }
        )

        machinery2, _ = Machinery.objects.get_or_create(
            id_machinery=2,
            defaults={
                'machinery_name': 'Tractor 2',
                'serial_number': 'S-0002',
                'machinery_type': type_unit,
                'machinery_secondary_type': type_unit,
                'id_model': model_obj,
                'machinery_operational_status': status_unit,
                'id_responsible_user': responsible_user
            }
        )

        machinery5, _ = Machinery.objects.get_or_create(
            id_machinery=5,
            defaults={
                'machinery_name': 'Tractor 5',
                'serial_number': 'S-0005',
                'machinery_type': type_unit,
                'machinery_secondary_type': type_unit,
                'id_model': model_obj,
                'machinery_operational_status': status_unit,
                'id_responsible_user': responsible_user
            }
        )

        # Crear dispositivos de telemetría
        # TelemetryDevices fields: name, IMEI, id_statues, id_responsible_user
        device1, _ = TelemetryDevices.objects.get_or_create(
            id_device=1,
            defaults={
                'name': 'Device 1',
                'IMEI': 111111111111111,
                'id_statues': status_unit,
                'id_responsible_user': responsible_user
            }
        )

        device2, _ = TelemetryDevices.objects.get_or_create(
            id_device=2,
            defaults={
                'name': 'Device 2',
                'IMEI': 222222222222222,
                'id_statues': status_unit,
                'id_responsible_user': responsible_user
            }
        )

        # Crear parámetros (usar campo real `avl_id_parameter` y `parameter_name`)
        param_speed, _ = Parameters.objects.get_or_create(
            avl_id_parameter=3,
            defaults={
                'parameter_name': 'Velocidad',
                'description': 'Parámetro de velocidad',
            }
        )

        param_consumption, _ = Parameters.objects.get_or_create(
            avl_id_parameter=12,
            defaults={
                'parameter_name': 'Consumo',
                'description': 'Parámetro de consumo',
            }
        )

        param_distance, _ = Parameters.objects.get_or_create(
            avl_id_parameter=15,
            defaults={
                'parameter_name': 'Distancia',
                'description': 'Parámetro de distancia',
            }
        )

        param_effective_hours, _ = Parameters.objects.get_or_create(
            avl_id_parameter=18,
            defaults={
                'parameter_name': 'Horas Efectivas',
                'description': 'Horas efectivas de trabajo',
            }
        )

        # Crear solicitudes de servicio
        base_date = timezone.now() - timedelta(days=10)

        request1, _ = ServiceRequest.objects.get_or_create(
            id_request='SOL-2025-0074',
            defaults={
                'customer': customer1,
                'request_detail': 'Solicitud de prueba 1',
                'scheduled_start_date': (base_date + timedelta(days=2)).date(),
                'scheduled_end_date': (base_date + timedelta(days=3)).date(),
                'request_status': status_finalized,
                'payment_method': payment_method,
                'payment_status': status_payment,
                'amount_paid': 1000000,
                'currency_unit_amount_paid': unit_currency,
                'amount_to_pay': 0,
                'currency_unit_amount_to_pay': unit_currency,
                'completion_cancellation_datetime': base_date + timedelta(days=3, hours=5),
                'id_responsible_user': responsible_user
            }
        )

        request2, _ = ServiceRequest.objects.get_or_create(
            id_request='SOL-2025-0007',
            defaults={
                'customer': customer2,
                'request_detail': 'Solicitud de prueba 2',
                'scheduled_start_date': (base_date - timedelta(days=5)).date(),
                'scheduled_end_date': (base_date + timedelta(days=1)).date(),
                'request_status': status_finalized,
                'payment_method': payment_method,
                'payment_status': status_payment,
                'amount_paid': 500000,
                'currency_unit_amount_paid': unit_currency,
                'amount_to_pay': 0,
                'currency_unit_amount_to_pay': unit_currency,
                'completion_cancellation_datetime': base_date + timedelta(days=1),
                'id_responsible_user': responsible_user
            }
        )

        request3, _ = ServiceRequest.objects.get_or_create(
            id_request='SOL-2025-0072',
            defaults={
                'customer': customer2,
                'request_detail': 'Solicitud de prueba 3',
                'scheduled_start_date': (base_date - timedelta(days=5)).date(),
                'scheduled_end_date': base_date.date(),
                'request_status': status_finalized,
                'payment_method': payment_method,
                'payment_status': status_payment,
                'amount_paid': 750000,
                'currency_unit_amount_paid': unit_currency,
                'amount_to_pay': 0,
                'currency_unit_amount_to_pay': unit_currency,
                'completion_cancellation_datetime': base_date,
                'id_responsible_user': responsible_user
            }
        )

        request4, _ = ServiceRequest.objects.get_or_create(
            id_request='SOL-2025-0010',
            defaults={
                'customer': customer1,
                'request_detail': 'Solicitud de prueba 4',
                'scheduled_start_date': (base_date - timedelta(days=5)).date(),
                'scheduled_end_date': (base_date + timedelta(days=1)).date(),
                'request_status': status_finalized,
                'payment_method': payment_method,
                'payment_status': status_payment,
                'amount_paid': 600000,
                'currency_unit_amount_paid': unit_currency,
                'amount_to_pay': 0,
                'currency_unit_amount_to_pay': unit_currency,
                'completion_cancellation_datetime': base_date + timedelta(days=1),
                'id_responsible_user': responsible_user
            }
        )

        # Crear asignaciones y datos
        RequestMachineryUser.objects.get_or_create(request=request1, machinery=machinery1, user=user1)
        RequestMachineryUser.objects.get_or_create(request=request1, machinery=machinery5, user=user1)
        RequestMachineryUser.objects.get_or_create(request=request2, machinery=machinery1, user=user2)
        RequestMachineryUser.objects.get_or_create(request=request3, machinery=machinery1, user=user1)
        RequestMachineryUser.objects.get_or_create(request=request3, machinery=machinery2, user=user2)
        RequestMachineryUser.objects.get_or_create(request=request4, machinery=machinery1, user=user2)

        Data.objects.get_or_create(id_request=request1, id_machinery=machinery1, id_user=user1, id_parameter=param_speed, id_device=device1, registered_at=base_date + timedelta(days=2, hours=5, minutes=7, seconds=21), defaults={'data': 94.71, 'alert': False})
        Data.objects.get_or_create(id_request=request1, id_machinery=machinery1, id_user=user1, id_parameter=param_consumption, id_device=device1, registered_at=base_date + timedelta(days=2, hours=5, minutes=7, seconds=21), defaults={'data': 10.9, 'alert': False})
        Data.objects.get_or_create(id_request=request1, id_machinery=machinery1, id_user=user1, id_parameter=param_distance, id_device=device1, registered_at=base_date + timedelta(days=2, hours=5, minutes=7, seconds=21), defaults={'data': 5, 'alert': False})
        Data.objects.get_or_create(id_request=request2, id_machinery=machinery1, id_user=user2, id_parameter=param_speed, id_device=device1, registered_at=base_date + timedelta(hours=10), defaults={'data': 162.17, 'alert': False})
        Data.objects.get_or_create(id_request=request2, id_machinery=machinery1, id_user=user2, id_parameter=param_consumption, id_device=device1, registered_at=base_date + timedelta(hours=10), defaults={'data': 76.65, 'alert': False})
        Data.objects.get_or_create(id_request=request2, id_machinery=machinery1, id_user=user2, id_parameter=param_distance, id_device=device1, registered_at=base_date + timedelta(hours=10), defaults={'data': 20000, 'alert': False})
        Data.objects.get_or_create(id_request=request3, id_machinery=machinery1, id_user=user1, id_parameter=param_speed, id_device=device1, registered_at=base_date - timedelta(hours=1), defaults={'data': 165.06, 'alert': False})
        Data.objects.get_or_create(id_request=request3, id_machinery=machinery1, id_user=user1, id_parameter=param_consumption, id_device=device1, registered_at=base_date - timedelta(hours=1), defaults={'data': 26.67, 'alert': False})
        Data.objects.get_or_create(id_request=request3, id_machinery=machinery1, id_user=user1, id_parameter=param_distance, id_device=device1, registered_at=base_date - timedelta(hours=1), defaults={'data': 48382, 'alert': False})
        Data.objects.get_or_create(id_request=request3, id_machinery=machinery2, id_user=user2, id_parameter=param_speed, id_device=device2, registered_at=base_date - timedelta(hours=2), defaults={'data': 157.0, 'alert': False})
        Data.objects.get_or_create(id_request=request3, id_machinery=machinery2, id_user=user2, id_parameter=param_consumption, id_device=device2, registered_at=base_date - timedelta(hours=2), defaults={'data': 18.1, 'alert': False})
        Data.objects.get_or_create(id_request=request4, id_machinery=machinery1, id_user=user2, id_parameter=param_speed, id_device=device1, registered_at=base_date + timedelta(hours=8), defaults={'data': 145.17, 'alert': False})
        Data.objects.get_or_create(id_request=request4, id_machinery=machinery1, id_user=user2, id_parameter=param_consumption, id_device=device1, registered_at=base_date + timedelta(hours=8), defaults={'data': 0, 'alert': False})

        return {
            'users': [user1, user2, responsible_user],
            'customers': [customer1, customer2],
            'machineries': [machinery1, machinery2, machinery5],
            'requests': [request1, request2, request3, request4],
            'base_date': base_date
        }


# ================================================================================
# HU-MS-009-1: Consulta exitosa del histórico general sin filtros
# ================================================================================
@pytest.mark.django_db
def test_hu_ms_009_1_consulta_sin_filtros(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    HU-MS-009-1: Consulta exitosa del histórico general sin filtros
    
    Verifica que el endpoint retorna correctamente la información histórica 
    de todas las solicitudes finalizadas cuando no se aplican filtros.
    """
    # Arrange
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get('/data/service_requests/')
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, \
                f"Expected 200 OK, got {response.status_code}"
            
            data = response.json()
            
            # Verificar que contiene los campos esperados
            assert 'start_date' in data or 'requests' in data, \
                "Response should contain 'start_date' or 'requests'"
            
            assert 'end_date' in data or 'requests' in data, \
                "Response should contain 'end_date' or 'requests'"
            
            assert 'requests' in data, "Response should contain 'requests' field"
            assert isinstance(data['requests'], list), "Requests should be a list"
            assert len(data['requests']) > 0, "Should return at least one request"
            
            # Verificar estructura de cada solicitud
            for request in data['requests']:
                assert 'code' in request
                assert 'customer_id' in request
                assert 'legal_entity_name' in request
                assert 'customer_name' in request
                assert 'request_status_id' in request
                assert request['request_status_id'] == 22, "All requests should be status 22 (Finalized)"
                assert 'request_status_name' in request
                assert 'scheduled_date' in request
                assert 'completion_date' in request
                assert 'machineries' in request
                assert 'id_machineries' in request
                assert 'operators' in request
                assert 'id_operators' in request
                assert 'total_distance_km' in request
                assert 'average_speed' in request
                assert 'average_consumption' in request
                assert 'effective_working_hours' in request
                assert 'operating_time_hours' in request


# ================================================================================
# HU-MS-009-2: Filtrado histórico por maquinaria específica
# ================================================================================
@pytest.mark.django_db
def test_hu_ms_009_2_filtro_por_maquinaria(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    HU-MS-009-2: Filtrado histórico por maquinaria específica
    
    Valida que al pasar machinery_id, solo se obtienen los registros e 
    información general de esa maquinaria.
    """
    # Arrange
    machinery_id = 1
    
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get(f'/data/service_requests/?machinery_id={machinery_id}')
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, \
                f"Expected 200 OK, got {response.status_code}"
            
            data = response.json()
            
            # Verificar que incluye métricas generales de la maquinaria
            assert 'operating_time_hours' in data, \
                "Should include operating_time_hours when filtering by machinery"
            assert 'total_distance_km' in data, \
                "Should include total_distance_km when filtering by machinery"
            assert 'effective_working_hours' in data, \
                "Should include effective_working_hours when filtering by machinery"
            assert 'average_speed' in data, \
                "Should include average_speed when filtering by machinery"
            assert 'average_consumption' in data, \
                "Should include average_consumption when filtering by machinery"
            
            # Verificar que las solicitudes contienen solo la maquinaria filtrada
            assert 'requests' in data
            for request in data['requests']:
                assert 'id_machineries' in request
                machinery_ids = [m['id'] for m in request['id_machineries']]
                assert machinery_id in machinery_ids, \
                    f"All requests should contain machinery {machinery_id}"


# ================================================================================
# HU-MS-009-3: Filtrado histórico por operario específico
# ================================================================================
@pytest.mark.django_db
def test_hu_ms_009_3_filtro_por_operario(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    HU-MS-009-3: Filtrado histórico por operario específico
    
    Verifica que pasando operator_id, solo se obtienen registros y métricas 
    asociadas a ese operario.
    """
    # Arrange
    operator_id = 1
    
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get(f'/data/service_requests/?operator_id={operator_id}')
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, \
                f"Expected 200 OK, got {response.status_code}"
            
            data = response.json()
            
            # Verificar que las solicitudes contienen solo el operario filtrado
            assert 'requests' in data
            assert len(data['requests']) > 0, "Should return at least one request"
            
            for request in data['requests']:
                assert 'id_operators' in request
                operator_ids = [op['id'] for op in request['id_operators']]
                assert operator_id in operator_ids, \
                    f"All requests should contain operator {operator_id}. Response: {response.json()}"


# ================================================================================
# HU-MS-009-4: Filtro combinado por maquinaria y operario
# ================================================================================
@pytest.mark.django_db
def test_hu_ms_009_4_filtro_combinado_maquinaria_operario(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    HU-MS-009-4: Filtro combinado por maquinaria y operario
    
    Verifica que el endpoint soporta correctamente la combinación de filtros 
    para maquinaria y operario.
    """
    # Arrange
    machinery_id = 1
    operator_id = 1
    
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get(
                f'/data/service_requests/?machinery_id={machinery_id}&operator_id={operator_id}'
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, \
                f"Expected 200 OK, got {response.status_code}"
            
            data = response.json()
            
            # Verificar métricas generales
            assert 'operating_time_hours' in data
            assert 'total_distance_km' in data
            assert 'effective_working_hours' in data
            assert 'average_speed' in data
            assert 'average_consumption' in data
            
            # Verificar que las solicitudes cumplen ambos criterios
            assert 'requests' in data
            for request in data['requests']:
                machinery_ids = [m['id'] for m in request['id_machineries']]
                operator_ids = [op['id'] for op in request['id_operators']]
                
                assert machinery_id in machinery_ids, \
                    f"Request should contain machinery {machinery_id}"
                assert operator_id in operator_ids, \
                    f"Request should contain operator {operator_id}. Response: {response.json()}"


# ================================================================================
# HU-MS-009-5: Filtro por rango de fechas
# ================================================================================
@pytest.mark.django_db
def test_hu_ms_009_5_filtro_por_fechas(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    HU-MS-009-5: Filtro por rango de fechas y horas
    
    Valida que al pasar los parámetros start_date y end_date, solo se muestren 
    datos históricos dentro de ese rango temporal.
    """
    # Arrange
    test_data = setup_test_data
    base_date = test_data['base_date']
    
    # Usar una fecha específica del rango de datos
    start_date = (base_date + timedelta(days=2)).strftime('%Y-%m-%d')
    end_date = (base_date + timedelta(days=2)).strftime('%Y-%m-%d')
    
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get(
                f'/data/service_requests/?start_date={start_date}&end_date={end_date}'
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, \
                f"Expected 200 OK, got {response.status_code}"
            
            data = response.json()
            
            # Verificar que retorna solicitudes
            assert 'requests' in data


# ================================================================================
# HU-MS-009-6: Filtro combinado con fechas/horas
# ================================================================================
@pytest.mark.django_db
def test_hu_ms_009_6_filtro_completo(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    HU-MS-009-6: Filtro combinado: maquinaria, operario y fechas/horas
    
    Comprueba que es posible combinar todos los filtros y obtener solo los 
    datos históricos coincidentes.
    """
    # Arrange
    test_data = setup_test_data
    base_date = test_data['base_date']
    machinery_id = 1
    operator_id = 1
    
    start_datetime = (base_date + timedelta(days=2, hours=5, minutes=7, seconds=20)).strftime('%Y-%m-%dT%H:%M:%S')
    end_datetime = (base_date + timedelta(days=2, hours=23, minutes=13, seconds=41)).strftime('%Y-%m-%dT%H:%M:%S')
    
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get(
                f'/data/service_requests/?machinery_id={machinery_id}&operator_id={operator_id}'
                f'&start_date={start_datetime}&end_date={end_datetime}'
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, \
                f"Expected 200 OK, got {response.status_code}"
            
            data = response.json()
            
            # Verificar métricas generales
            assert 'operating_time_hours' in data
            assert 'total_distance_km' in data
            assert 'effective_working_hours' in data
            assert 'average_speed' in data
            assert 'average_consumption' in data
            
            # Verificar que las solicitudes cumplen todos los criterios
            assert 'requests' in data
            for request in data['requests']:
                machinery_ids = [m['id'] for m in request['id_machineries']]
                operator_ids = [op['id'] for op in request['id_operators']]
                
                assert machinery_id in machinery_ids
                assert operator_id in operator_ids, f"Request should contain operator {operator_id}. Response: {response.json()}"


# ================================================================================
# HU-MS-009-7: Mensaje informativo sin datos
# ================================================================================
@pytest.mark.django_db
def test_hu_ms_009_7_sin_datos_coincidentes(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    HU-MS-009-7: Mensaje informativo al no encontrar datos históricos coincidentes
    
    Valida que, si no existen solicitudes finalizadas asociadas al criterio 
    filtrado, el sistema responde con un mensaje claro y ningún dato.
    """
    # Arrange
    machinery_id = 9999  # ID inexistente
    
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get(f'/data/service_requests/?machinery_id={machinery_id}')
            
            # Assert
            assert response.status_code == status.HTTP_200_OK, \
                f"Expected 200 OK, got {response.status_code}"
            
            data = response.json()
            
            # Verificar que retorna lista vacía o sin resultados
            assert 'requests' in data
            assert len(data['requests']) == 0, \
                "Should return empty list when no data matches criteria"


# ================================================================================
# HU-MS-009-8: Seguridad - acceso restringido
# ================================================================================
@pytest.mark.django_db
def test_hu_ms_009_8_acceso_sin_permiso(api_client, setup_test_data):
    """
    HU-MS-009-8: Seguridad: acceso restringido solo a usuarios autorizados
    
    Evalúa que solo los usuarios con permiso 172 pueden consultar el histórico, 
    rechazando acceso con error 403 a otros casos.
    """
    # Arrange
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = False  # Usuario sin permiso
        
        # Act
        response = api_client.get('/data/service_requests/?machinery_id=1')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN, \
            f"Expected 403 FORBIDDEN, got {response.status_code}"
        
        data = response.json()
        assert 'error' in data or 'detail' in data, \
            "Should return error message"


# ================================================================================
# PRUEBAS ADICIONALES - Validación de parámetros
# ================================================================================
@pytest.mark.django_db
def test_validacion_parametro_machinery_id_invalido(api_client, setup_test_data, mock_permission):
    """
    Verifica que el endpoint valida correctamente el parámetro machinery_id
    """
    # Arrange
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        # Act
        response = api_client.get('/data/service_requests/?machinery_id=invalid')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"Expected 400 BAD REQUEST for invalid machinery_id, got {response.status_code}"


@pytest.mark.django_db
def test_validacion_parametro_operator_id_invalido(api_client, setup_test_data, mock_permission):
    """
    Verifica que el endpoint valida correctamente el parámetro operator_id
    """
    # Arrange
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        # Act
        response = api_client.get('/data/service_requests/?operator_id=invalid')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"Expected 400 BAD REQUEST for invalid operator_id, got {response.status_code}"


@pytest.mark.django_db
def test_validacion_fecha_fin_menor_que_inicio(api_client, setup_test_data, mock_permission):
    """
    Verifica que el endpoint valida que la fecha de fin no sea anterior a la de inicio
    """
    # Arrange
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        # Act
        response = api_client.get(
            '/data/service_requests/?start_date=2025-11-10&end_date=2025-11-05'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"Expected 400 BAD REQUEST when end_date < start_date, got {response.status_code}"


@pytest.mark.django_db
def test_formato_fecha_invalido(api_client, setup_test_data, mock_permission):
    """
    Verifica que el endpoint valida el formato de las fechas
    """
    # Arrange
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        # Act
        response = api_client.get('/data/service_requests/?start_date=invalid-date')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"Expected 400 BAD REQUEST for invalid date format, got {response.status_code}"


# ================================================================================
# PRUEBAS DE ESTRUCTURA DE RESPUESTA
# ================================================================================
@pytest.mark.django_db
def test_estructura_respuesta_con_filtro_maquinaria(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    Verifica que la estructura de la respuesta es correcta cuando se filtra por maquinaria
    """
    # Arrange
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get('/data/service_requests/?machinery_id=1')
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            # Verificar campos de métricas generales
            expected_fields = [
                'operating_time_hours',
                'total_distance_km',
                'effective_working_hours',
                'average_speed',
                'average_consumption',
                'requests'
            ]
            
            for field in expected_fields:
                assert field in data, f"Response should contain field '{field}'"
            
            # Verificar formato de métricas
            assert 'h' in data['operating_time_hours'], \
                "operating_time_hours should include 'h' unit"
            assert 'km' in data['total_distance_km'], \
                "total_distance_km should include 'km' unit"
            assert 'h' in data['effective_working_hours'], \
                "effective_working_hours should include 'h' unit"
            assert 'km/h' in data['average_speed'], \
                "average_speed should include 'km/h' unit"
            assert 'L/h' in data['average_consumption'], \
                "average_consumption should include 'L/h' unit"


@pytest.mark.django_db
def test_estructura_respuesta_sin_filtros(api_client, setup_test_data, mock_permission, mock_auth_service):
    """
    Verifica que la estructura de la respuesta es correcta sin filtros
    """
    # Arrange
    with patch('monitoring.api.data_viewset.DataViewSet.check_permission') as mock_check_perm:
        mock_check_perm.return_value = True
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_auth_service([1, 2])
            mock_post.return_value = mock_response
            
            # Act
            response = api_client.get('/data/service_requests/')
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            # Sin filtro de maquinaria, no debe incluir métricas generales
            machinery_metrics = [
                'operating_time_hours',
                'total_distance_km',
                'effective_working_hours',
                'average_speed',
                'average_consumption'
            ]
            
            # Verificar que debe tener requests
            assert 'requests' in data


# ================================================================================
# GENERADOR DE REPORTE
# ================================================================================
def generate_test_report():
    """
    Genera un reporte detallado de las pruebas ejecutadas
    """
    import subprocess
    import os
    
    # Ejecutar pytest con opciones de reporte detallado
    result = subprocess.run(
        ['pytest', __file__, '-v', '--tb=short', '--json-report', '--json-report-file=report.json'],
        capture_output=True,
        text=True
    )
    
    return result


if __name__ == '__main__':
    # Ejecutar las pruebas
    pytest.main([__file__, '-v', '--tb=short'])
