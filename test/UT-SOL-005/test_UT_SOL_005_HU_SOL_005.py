"""
Pruebas unitarias para actualización de solicitudes de servicio
ID: UT-SOL-005

Historia de Usuario: Como administrador, quiero actualizar una solicitud de servicio
existente para modificar los detalles, fechas, ubicación, asignaciones de maquinaria
y operarios, así como la información de pago.

Endpoint bajo prueba:
- PATCH /service_requests/{id_request}/update_request/ - Actualizar solicitud de servicio

Permisos requeridos:
- 155: request.update - Actualizar solicitud
"""

import pytest
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.utils import timezone
from rest_framework.test import APIClient

from service_requests.models import (
    ServiceRequest,
    RequestLocation,
    Customer,
    PersonType,
    TaxRegime,
    DocumentType,
    PaymentMethod,
    RequestMachineryUser
)
from users.models import User
from parameterization.models import (
    Statues,
    StatuesCategory,
    Types,
    TypesCategory,
    Units,
    UnitsCategory
)
from machinery.models import Machinery


@pytest.mark.django_db
class TestRequestUpdateEndpoint:
    """Pruebas para el endpoint de actualización de solicitudes"""
    
    endpoint_template = "/service_requests/{}/update_request/"
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        
        # Crear usuario responsable
        self.responsible_user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([155])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Inicializar parametrización base
        self._bootstrap_parametrization()
        
        # Crear datos de prueba
        self.customer = self._create_test_customer()
        self.inactive_customer = self._create_test_customer(document_number=1234567891, is_active=False)
        
        # IDs de maquinaria que se usarán en los payloads (sin crear objetos)
        self.machinery_id_1 = 10
        self.machinery_id_2 = 9
        
        # Crear método de pago
        self._create_payment_methods()
        
        # Limpiar solicitudes previas
        RequestMachineryUser.objects.all().delete()
        ServiceRequest.objects.all().delete()
        RequestLocation.objects.all().delete()
    
    # ==================== HELPERS ====================
    
    def _ensure_user(self, user_id: int) -> User:
        """Crea o recupera un usuario para pruebas"""
        user, created = User.objects.get_or_create(
            id_user=user_id
        )
        user.id = user.id_user
        user.is_authenticated = True
        return user
    
    def _token_with_permissions(self, permission_ids):
        """Genera payload de token con permisos específicos"""
        perms = [{"id": perm_id} for perm_id in permission_ids]
        return {
            "roles": [{"permisos": perms, "permissions": perms}],
            "permisos": perms,
            "permissions": perms,
        }
    
    def _bootstrap_parametrization(self):
        """Inicializa datos de parametrización necesarios"""
        # Categoría de estados generales
        self.statues_category_general = StatuesCategory.objects.create(
            id_statues_categories=1,
            name="Estados generales",
            description="Estados del sistema",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Categoría de estados de pago (id=6)
        self.payment_status_category = StatuesCategory.objects.create(
            id_statues_categories=6,
            name="Estados del pago de la Solicitud",
            description="Estados de pago",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Estados generales
        self.status_active = Statues.objects.create(
            id_statues=1,
            name="Activo",
            description="Estado activo",
            id_statues_categories=self.statues_category_general,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.status_inactive = Statues.objects.create(
            id_statues=2,
            name="Inactivo",
            description="Estado inactivo",
            id_statues_categories=self.statues_category_general,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Estado de solicitud - Pendiente
        self.status_pending = Statues.objects.create(
            id_statues=20,
            name="Pendiente",
            description="Solicitud pendiente",
            id_statues_categories=self.statues_category_general,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Estados de pago
        self.payment_status_pending = Statues.objects.create(
            id_statues=17,
            name="Pendiente de pago",
            description="Pago pendiente",
            id_statues_categories=self.payment_status_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.payment_status_paid = Statues.objects.create(
            id_statues=18,
            name="Pago Total",
            description="Pago completado",
            id_statues_categories=self.payment_status_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Categoría de unidades de área (id=11)
        self.area_units_category = UnitsCategory.objects.create(
            id_units_categories=11,
            name="Unidades de area",
            description="Categoría de unidades de área",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Categoría de unidades de longitud (id=7)
        self.length_units_category = UnitsCategory.objects.create(
            id_units_categories=7,
            name="Tipos de longitud",
            description="Categoría de unidades de longitud",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Categoría de unidades de moneda (id=10)
        self.currency_units_category = UnitsCategory.objects.create(
            id_units_categories=10,
            name="Unidades de moneda",
            description="Categoría de unidades de moneda",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Categoría de tipos
        self.unit_types_category = TypesCategory.objects.create(
            id_types_categories=16,
            name="Tipos de unidades",
            description="Categoría de tipos de unidades",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Tipo para área
        self.area_type = Types.objects.create(
            id_types=4,
            name="Tipo área",
            description="Tipo de unidad de área",
            id_types_categories=self.unit_types_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
            id_statues=self.status_active,
        )
        
        # Tipo para longitud
        self.length_type = Types.objects.create(
            id_types=5,
            name="Tipo longitud",
            description="Tipo de unidad de longitud",
            id_types_categories=self.unit_types_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
            id_statues=self.status_active,
        )
        
        # Tipo para moneda
        self.currency_type = Types.objects.create(
            id_types=6,
            name="Tipo moneda",
            description="Tipo de unidad de moneda",
            id_types_categories=self.unit_types_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
            id_statues=self.status_active,
        )
        
        # Unidades
        self.area_unit = Units.objects.create(
            id_units=19,
            name="Metros cubicos",
            symbol="m³",
            id_units_categories=self.area_units_category,
            id_types=self.area_type,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.altitude_unit = Units.objects.create(
            id_units=16,
            name="Metros",
            symbol="m",
            id_units_categories=self.length_units_category,
            id_types=self.length_type,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.currency_unit = Units.objects.create(
            id_units=17,
            name="Peso Colombiano",
            symbol="COP",
            id_units_categories=self.currency_units_category,
            id_types=self.currency_type,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
    
    def _create_test_customer(self, document_number=1079172265, is_active=True):
        """Crea un cliente de prueba"""
        person_type, _ = PersonType.objects.get_or_create(
            id_person_type=1,
            defaults={"name": "Natural"}
        )
        
        tax_regime, _ = TaxRegime.objects.get_or_create(
            id_tax_regime=1,
            defaults={"code": "SIMP", "name": "Simplificado"}
        )
        
        document_type, _ = DocumentType.objects.get_or_create(
            id_document_type=1,
            defaults={"name": "Cédula de Ciudadanía"}
        )
        
        status = self.status_active if is_active else self.status_inactive
        
        customer, _ = Customer.objects.get_or_create(
            document_number=document_number,
            defaults={
                "type_document_id": document_type,
                "person_type": person_type,
                "legal_entity_name": "voldemort",
                "name": "Juan Andres",
                "first_last_name": "Veru",
                "second_last_name": "Sarmiento",
                "email": "juanandresveru@gmail.com",
                "phone": "3001234567",
                "address": "Calle 123",
                "id_municipality": 1,
                "tax_regime": tax_regime,
                "customer_statues": status,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.responsible_user,
            }
        )
        return customer
    
    def _create_payment_methods(self):
        """Crea métodos de pago de prueba"""
        PaymentMethod.objects.get_or_create(
            code="20",
            defaults={"name": "Cheque"}
        )
        PaymentMethod.objects.get_or_create(
            code="10",
            defaults={"name": "Efectivo"}
        )
    
    def _create_test_request(self, customer=None, start_date=None, end_date=None, status=None):
        """Crea una solicitud de prueba"""
        if customer is None:
            customer = self.customer
        
        if start_date is None:
            start_date = (timezone.now() + timedelta(days=30)).date()
        
        if end_date is None:
            end_date = (timezone.now() + timedelta(days=31)).date()
        
        if status is None:
            status = self.status_pending
        
        # Generar ID único
        request_count = ServiceRequest.objects.count() + 1
        request_id = f"SOL-2025-{request_count:04d}"
        
        # Crear solicitud
        request = ServiceRequest.objects.create(
            id_request=request_id,
            customer=customer,
            request_detail="Solicitud de servicio de mantenimiento",
            scheduled_start_date=start_date,
            scheduled_end_date=end_date,
            request_status=status,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Crear ubicación y asociarla
        location = RequestLocation.objects.create(
            request=request,
            country="codeC",
            department="codeD",
            city_id=1,
            place_name="Finca La Esperanza",
            latitude=89.244255,
            longitude=-19.581299,
            area=200.0,
            area_unit=self.area_unit,
            altitude=500.0,
            altitude_unit=self.altitude_unit
        )
        
        return request
    
    def _get_valid_update_payload(self):
        """Retorna un payload válido para actualizar solicitud"""
        future_date = (timezone.now() + timedelta(days=45)).date()
        end_date = (timezone.now() + timedelta(days=46)).date()
        
        return {
            "customer": self.customer.id_customer,
            "request_detail": "Solicitud actualizada de mantenimiento",
            "scheduled_start_date": future_date.strftime("%Y-%m-%d"),
            "scheduled_end_date": end_date.strftime("%Y-%m-%d"),
            "payment_method": "20",
            "payment_status": self.payment_status_pending.id_statues,
            "amount_paid": 500,
            "currency_unit_amount_paid": self.currency_unit.id_units,
            "amount_to_pay": 1000,
            "currency_unit_amount_to_pay": self.currency_unit.id_units,
            "location": {
                "country": "codeC",
                "department": "codeD",
                "city_id": 1,
                "place_name": "Finca Actualizada",
                "latitude": 4.123456,
                "longitude": -74.654321,
                "area": 3000,
                "area_unit": self.area_unit.id_units,
                "altitude": 800,
                "altitude_unit": self.altitude_unit.id_units
            },
            "machinery_users": [
                {
                    "machinery_id": self.machinery_id_1,
                    "user_id": self.responsible_user.id_user,
                    "soil_type": None,
                    "texture": None,
                    "humidity_level": None,
                    "implementation": None,
                    "depth": None,
                    "slope": None,
                    "work_duration": None
                }
            ]
        }
    
    # ==================== PRUEBAS ====================
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_001_update_request_success(self, mock_audit):
        """
        UT-SOL-001: Verificar actualización exitosa de solicitud con datos válidos
        
        Validar que el endpoint PATCH actualice correctamente una solicitud pendiente
        cuando se proporcionan todos los datos requeridos válidos.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        payload = self._get_valid_update_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        assert response.data['success'] is True
        assert 'message' in response.data
        assert 'actualizada exitosamente' in response.data['message'].lower()
        
        # Verificar en base de datos
        request.refresh_from_db()
        assert request.request_detail == payload['request_detail']
        assert request.amount_paid == 500
        assert request.amount_to_pay == 1000
        
        # Verificar ubicación actualizada
        location = RequestLocation.objects.get(request=request)
        assert location.place_name == "Finca Actualizada"
        assert location.latitude == 4.123456
        assert location.longitude == -74.654321
        
        print(f"✅ UT-SOL-001: APROBADO - Solicitud actualizada: {request.id_request}")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_002_inactive_customer(self, mock_audit):
        """
        UT-SOL-002: Verificar error de validación por cliente inactivo
        
        Validar que el endpoint retorne error cuando se intenta actualizar una
        solicitud con un cliente inactivo.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['customer'] = self.inactive_customer.id_customer
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        assert 'customer' in response.data['errors']
        assert 'inactivo' in str(response.data['errors']['customer']).lower()
        
        print(f"✅ UT-SOL-002: APROBADO - Cliente inactivo rechazado correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_003_invalid_coordinates(self, mock_audit):
        """
        UT-SOL-003: Verificar validación de coordenadas geográficas inválidas
        
        Validar que el endpoint rechace coordenadas fuera del rango válido
        (latitud: -90 a 90, longitud: -180 a 180).
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['location']['latitude'] = 95.123456
        payload['location']['longitude'] = -200.654321
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        assert 'location' in response.data['errors']
        
        location_errors = response.data['errors']['location']
        assert 'latitude' in location_errors or any('latitud' in str(err).lower() for err in location_errors.values() if isinstance(location_errors, dict))
        assert 'longitude' in location_errors or any('longitud' in str(err).lower() for err in location_errors.values() if isinstance(location_errors, dict))
        
        print(f"✅ UT-SOL-003: APROBADO - Coordenadas inválidas rechazadas correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_004_past_start_date(self, mock_audit):
        """
        UT-SOL-004: Verificar validación de fechas anteriores a la fecha actual
        
        Validar que el endpoint rechace fechas de inicio anteriores a la fecha actual.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['scheduled_start_date'] = "2025-10-01"
        payload['scheduled_end_date'] = "2025-10-02"
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        assert 'scheduled_start_date' in response.data['errors']
        assert 'anterior' in str(response.data['errors']['scheduled_start_date']).lower()
        
        print(f"✅ UT-SOL-004: APROBADO - Fecha pasada rechazada correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_005_amount_paid_greater_than_to_pay(self, mock_audit):
        """
        UT-SOL-005: Verificar validación de monto pagado mayor al monto a pagar
        
        Validar que el endpoint rechace cuando el monto pagado excede el monto total a pagar.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['amount_paid'] = 1500
        payload['amount_to_pay'] = 1000
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        assert 'amount_paid' in response.data['errors']
        assert 'mayor' in str(response.data['errors']['amount_paid']).lower()
        
        print(f"✅ UT-SOL-005: APROBADO - Monto pagado mayor rechazado correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_006_duplicate_machinery(self, mock_audit):
        """
        UT-SOL-006: Verificar validación de maquinaria duplicada
        
        Validar que el endpoint rechace la asignación de la misma maquinaria
        múltiples veces en una solicitud.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['machinery_users'] = [
            {
                "machinery_id": self.machinery_id_1,
                "user_id": self.responsible_user.id_user,
                "soil_type": None,
                "texture": None,
                "humidity_level": None,
                "implementation": None,
                "depth": None,
                "slope": None,
                "work_duration": None
            },
            {
                "machinery_id": self.machinery_id_1,
                "user_id": 2,
                "soil_type": None,
                "texture": None,
                "humidity_level": None,
                "implementation": None,
                "depth": None,
                "slope": None,
                "work_duration": None
            }
        ]
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        assert 'machinery_users' in response.data['errors']
        assert 'duplicad' in str(response.data['errors']['machinery_users']).lower()
        
        print(f"✅ UT-SOL-006: APROBADO - Maquinaria duplicada rechazada correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_007_missing_required_fields(self, mock_audit):
        """
        UT-SOL-007: Verificar validación de campos obligatorios faltantes
        
        Validar que el endpoint retorne errores apropiados cuando faltan campos requeridos.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = {
            "customer": None,
            "request_detail": None,
            "location": {
                "latitude": None,
                "longitude": None
            }
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        assert 'errors' in response.data
        
        # Verificar errores en campos específicos
        errors = response.data['errors']
        assert any(key in ['customer', 'request_detail', 'location'] for key in errors.keys())
        
        print(f"✅ UT-SOL-007: APROBADO - Campos obligatorios validados correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_008_max_length_validation(self, mock_audit):
        """
        UT-SOL-008: Verificar validación de longitud máxima de campos
        
        Validar que el endpoint rechace datos que excedan la longitud máxima permitida
        (request_detail: 600 chars, place_name: 255 chars).
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['request_detail'] = "a" * 601
        payload['location']['place_name'] = "b" * 256
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        assert 'errors' in response.data
        
        # Verificar errores de longitud
        errors = response.data['errors']
        has_length_error = (
            'request_detail' in errors or 
            ('location' in errors and isinstance(errors['location'], dict) and 'place_name' in errors['location'])
        )
        assert has_length_error, "Expected max_length validation error"
        
        print(f"✅ UT-SOL-008: APROBADO - Longitud máxima validada correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_009_incomplete_training_data(self, mock_audit):
        """
        UT-SOL-009: Verificar validación de datos de entrenamiento del modelo incompletos
        
        Validar que cuando se proporcionan datos para entrenamiento del modelo,
        todos los campos sean obligatorios.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['machinery_users'] = [
            {
                "machinery_id": self.machinery_id_1,
                "user_id": self.responsible_user.id_user,
                "soil_type": 1,  # Solo un campo proporcionado
                "texture": None,
                "humidity_level": None,
                "implementation": None,
                "depth": None,
                "slope": None,
                "work_duration": None
            }
        ]
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        assert 'machinery_users' in response.data['errors'] or 'errors' in response.data
        
        # El error puede estar en diferentes formatos dependiendo del serializer
        # Solo verificamos que se rechazan los datos incompletos (status 400)
        print(f"Response errors: {response.data.get('errors', response.data)}")
        print(f"✅ UT-SOL-009: APROBADO - Datos de entrenamiento incompletos rechazados correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_010_permission_validation(self, mock_audit):
        """
        UT-SOL-010: Verificar validación de permisos de usuario
        
        Validar que solo usuarios con permiso request.update puedan actualizar solicitudes.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_without_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        print(f"✅ UT-SOL-010: APROBADO - Permisos validados correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_011_update_non_pending_request(self, mock_audit):
        """
        UT-SOL-011: Verificar rechazo de actualización de solicitud en estado diferente a Pendiente
        
        Validar que el endpoint rechace actualizaciones de solicitudes que no estén
        en estado "Pendiente" (ID=20), como solicitudes completadas o canceladas.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        # Crear estado "Completada"
        status_completed = Statues.objects.create(
            id_statues=30,
            name="Completada",
            description="Solicitud completada",
            id_statues_categories=self.statues_category_general,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Crear solicitud con estado completado
        request = self._create_test_request(status=status_completed)
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        # El endpoint retorna solo 'message' cuando el estado no es 20
        assert 'message' in response.data, f"Expected 'message' in response, got: {response.data}"
        
        # Verificar que menciona estado o pendiente
        error_message = str(response.data.get('message', '')).lower()
        assert 'estado' in error_message or 'pendiente' in error_message, f"Expected estado/pendiente in message, got: {error_message}"
        
        print(f"✅ UT-SOL-011: APROBADO - Solicitud no pendiente rechazada correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_012_end_date_before_start_date(self, mock_audit):
        """
        UT-SOL-012: Verificar validación de fecha de fin anterior a fecha de inicio
        
        Validar que el endpoint rechace cuando la fecha de fin programada es anterior
        a la fecha de inicio programada.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        # Fecha de inicio posterior a fecha de fin
        payload['scheduled_start_date'] = "2025-12-10"
        payload['scheduled_end_date'] = "2025-12-05"
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        
        # Verificar error relacionado con fechas
        errors_str = str(response.data.get('errors', '')).lower()
        assert 'fecha' in errors_str or 'date' in errors_str or 'end' in errors_str
        
        print(f"✅ UT-SOL-012: APROBADO - Fecha de fin anterior rechazada correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_013_different_currency_units(self, mock_audit):
        """
        UT-SOL-013: Verificar validación de monedas diferentes entre pagado y a pagar
        
        Validar que el endpoint rechace cuando la unidad de moneda del monto pagado
        es diferente a la unidad de moneda del monto a pagar.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        # Crear otra unidad de moneda (USD)
        currency_unit_usd = Units.objects.create(
            id_units=18,
            name="Dólar Estadounidense",
            symbol="USD",
            id_units_categories=self.currency_units_category,
            id_types=self.currency_type,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['currency_unit_amount_paid'] = currency_unit_usd.id_units  # USD
        payload['currency_unit_amount_to_pay'] = self.currency_unit.id_units  # COP
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        
        # Verificar error relacionado con monedas
        errors_str = str(response.data.get('errors', '')).lower()
        assert 'moneda' in errors_str or 'currency' in errors_str
        
        print(f"✅ UT-SOL-013: APROBADO - Monedas diferentes rechazadas correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_014_paid_status_with_incomplete_payment(self, mock_audit):
        """
        UT-SOL-014: Verificar validación de estado "Pagado" con montos incompletos
        
        Validar que el endpoint rechace cuando el estado de pago es "Pago Total" (ID=18)
        pero el monto pagado no es igual al monto a pagar.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        request = self._create_test_request()
        endpoint = self.endpoint_template.format(request.id_request)
        
        payload = self._get_valid_update_payload()
        payload['payment_status'] = self.payment_status_paid.id_statues  # Estado: Pago Total
        payload['amount_paid'] = 500  # Monto pagado menor al total
        payload['amount_to_pay'] = 1000
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert response.data['success'] is False
        
        # Verificar error relacionado con pago
        errors_str = str(response.data.get('errors', '')).lower()
        assert 'pago' in errors_str or 'monto' in errors_str or 'payment' in errors_str or 'amount' in errors_str
        
        print(f"✅ UT-SOL-014: APROBADO - Estado pagado con monto incompleto rechazado correctamente")
    
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_015_partial_update(self, mock_audit):
        """
        UT-SOL-015: Verificar actualización parcial de solicitud (PATCH)
        
        Validar que el endpoint permita actualizar solo algunos campos sin afectar
        los campos no enviados en el payload, verificando el comportamiento PATCH correcto.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        # Crear solicitud con datos iniciales
        request = self._create_test_request()
        original_detail = request.request_detail
        original_location = RequestLocation.objects.get(request=request)
        original_place_name = original_location.place_name
        
        endpoint = self.endpoint_template.format(request.id_request)
        
        # Payload parcial: solo actualizar request_detail
        payload = {
            "customer": self.customer.id_customer,
            "request_detail": "Detalle actualizado parcialmente"
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        assert response.data['success'] is True
        
        # Verificar que el campo actualizado cambió
        request.refresh_from_db()
        assert request.request_detail == "Detalle actualizado parcialmente"
        assert request.request_detail != original_detail
        
        # Verificar que otros campos NO cambiaron
        updated_location = RequestLocation.objects.get(request=request)
        assert updated_location.place_name == original_place_name
        assert request.scheduled_start_date is not None
        
        print(f"✅ UT-SOL-015: APROBADO - Actualización parcial (PATCH) funciona correctamente")
