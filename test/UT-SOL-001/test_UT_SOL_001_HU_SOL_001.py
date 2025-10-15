"""
Pruebas unitarias para creación de presolicitudes de servicio
ID: UT-SOL-001

Historia de Usuario: Como cliente, quiero crear una presolicitud de servicio
para solicitar maquinaria agrícola proporcionando los detalles del terreno,
fechas programadas y ubicación geográfica.

Endpoint bajo prueba:
- POST /service_requests/create_pre_request/ - Crear presolicitud de servicio

Permisos requeridos:
- 145: request.create_pre_register - Crear pre registro
- 148: request.pre_request_notify - Recibir notificaciones de pre-registro
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
    DocumentType
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


@pytest.mark.django_db
class TestPreRequestCreateEndpoint:
    """Pruebas para el endpoint de creación de presolicitudes"""
    
    endpoint = "/service_requests/create_pre_request/"
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        
        # Crear usuario responsable
        self.responsible_user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([145])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Inicializar parametrización base
        self._bootstrap_parametrization()
        
        # Crear cliente de prueba
        self.customer = self._create_test_customer()
        
        # Limpiar solicitudes previas
        ServiceRequest.objects.all().delete()
        RequestLocation.objects.all().delete()
    
    # ==================== HELPERS ====================
    
    def _ensure_user(self, user_id: int) -> User:
        """Crea o recupera un usuario para pruebas"""
        user = User.objects.create(id_user=user_id)
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
        # Categoría de estados
        self.statues_category = StatuesCategory.objects.create(
            id_statues_categories=1,
            name="Estados generales",
            description="Estados del sistema",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Estados
        self.status_active = Statues.objects.create(
            id_statues=1,
            name="Activo",
            description="Estado activo",
            id_statues_categories=self.statues_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.status_inactive = Statues.objects.create(
            id_statues=2,
            name="Inactivo",
            description="Estado inactivo",
            id_statues_categories=self.statues_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.status_pre_request = Statues.objects.create(
            id_statues=19,
            name="Presolicitud",
            description="Estado de presolicitud",
            id_statues_categories=self.statues_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Categorías de unidades
        self.area_units_category = UnitsCategory.objects.create(
            id_units_categories=11,
            name="Unidades de area",
            description="Categoría de unidades de área",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.length_units_category = UnitsCategory.objects.create(
            id_units_categories=7,
            name="Tipos de longitud",
            description="Categoría de unidades de longitud",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Categoría de tipos de suelo
        self.soil_types_category = TypesCategory.objects.create(
            id_types_categories=15,
            name="Tipos de suelos",
            description="Categoría de tipos de suelo",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Tipo de suelo (necesita tener id_statues)
        self.soil_type = Types.objects.create(
            id_types=3,
            name="Arcilloso",
            description="Suelo arcilloso",
            id_types_categories=self.soil_types_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
            id_statues=self.status_active,
        )
        
        # Categoría de tipos para unidades
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
        
        # Unidades (necesitan id_types e id_statues)
        self.area_unit = Units.objects.create(
            id_units=1,
            name="Hectáreas",
            symbol="ha",
            id_units_categories=self.area_units_category,
            id_types=self.area_type,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.altitude_unit = Units.objects.create(
            id_units=2,
            name="Metros",
            symbol="m",
            id_units_categories=self.length_units_category,
            id_types=self.length_type,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
    
    def _create_test_customer(self, document_number=1079172265, is_active=True):
        """Crea un cliente de prueba"""
        # Tipo de persona (compartido entre pruebas)
        person_type, _ = PersonType.objects.get_or_create(
            id_person_type=1,
            defaults={"name": "Natural"}
        )
        
        # Régimen tributario (compartido entre pruebas)
        tax_regime, _ = TaxRegime.objects.get_or_create(
            id_tax_regime=1,
            defaults={"code": "SIMP", "name": "Simplificado"}
        )
        
        # Tipo de documento (compartido entre pruebas)
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
                "legal_entity_name": "Juan Camilo Sarmiento Cardozo",
                "name": "Juan camilo",
                "first_last_name": "Sarmiento",
                "second_last_name": "Cardozo",
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
    
    def _get_valid_payload(self):
        """Retorna un payload válido para crear presolicitud"""
        future_date = (timezone.now() + timedelta(days=6)).date()
        end_date = (timezone.now() + timedelta(days=11)).date()
        
        return {
            "customer": self.customer.id_customer,  # Usar ID del customer, no document_number
            "request_detail": "Servicio de arado y preparación de terreno para cultivo de maíz",
            "scheduled_start_date": future_date.strftime("%Y-%m-%d"),
            "scheduled_end_date": end_date.strftime("%Y-%m-%d"),
            "location": {
                "country": "Colombia",
                "department": "Cundinamarca",
                "city_id": 1,
                "place_name": "Vereda Topacio",
                "latitude": "4.710989",
                "longitude": "-74.072092",
                "area": "15.5",
                "area_unit": self.area_unit.id_units,
                "soil_type": self.soil_type.id_types,
                "humidity_level": 75,
                "altitude": 2640,
                "altitude_unit": self.altitude_unit.id_units
            }
        }
    
    # ==================== PRUEBAS ====================
    
    @patch('service_requests.api.service_request_viewset.requests.post')
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_001_create_pre_request_success(self, mock_audit, mock_requests_post):
        """
        UT-SOL-001: Verificar creación exitosa de presolicitud con datos válidos completos
        
        Validar que el endpoint crea correctamente una presolicitud cuando se proporcionan
        todos los datos requeridos y válidos, generando el código de seguimiento único
        y notificaciones correspondientes.
        """
        # Arrange
        mock_requests_post.return_value = MagicMock(status_code=200)
        mock_audit.return_value.create = MagicMock()
        
        payload = self._get_valid_payload()
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer fake-token')
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': 'Bearer fake-token'}
        )
        
        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.data}"
        assert response.data['success'] is True
        assert 'id_request' in response.data
        assert response.data['id_request'].startswith('SOL-2025-')
        
        # Verificar en base de datos
        service_request = ServiceRequest.objects.get(id_request=response.data['id_request'])
        assert service_request.customer.document_number == self.customer.document_number
        assert service_request.request_status.id_statues == 19
        assert service_request.request_detail == payload['request_detail']
        
        # Verificar ubicación
        location = RequestLocation.objects.get(request=service_request)
        assert location.country == "Colombia"
        assert location.latitude == 4.710989
        assert location.longitude == -74.072092
        assert location.area == 15.5
        
        print(f"✅ UT-SOL-001: APROBADO - Presolicitud creada: {response.data['id_request']}")
    
    def test_ut_sol_002_customer_not_found(self):
        """
        UT-SOL-002: Verificar validación de cliente no registrado
        
        Validar que el sistema rechaza presolicitudes cuando el número de documento
        no corresponde a un cliente registrado.
        """
        # Arrange
        payload = self._get_valid_payload()
        payload['customer'] = 9999999999  # Documento no existente
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'errors' in response.data
        assert 'customer' in response.data['errors']
        
        print(f"✅ UT-SOL-002: APROBADO - Cliente no encontrado rechazado correctamente")
    
    def test_ut_sol_003_inactive_customer(self):
        """
        UT-SOL-003: Verificar validación de cliente inactivo
        
        Validar que el sistema rechaza presolicitudes de clientes inactivos.
        """
        # Arrange
        inactive_customer = self._create_test_customer(document_number=1234567890, is_active=False)
        
        payload = self._get_valid_payload()
        payload['customer'] = inactive_customer.id_customer  # Usar ID, no document_number
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'customer' in response.data['errors']
        assert 'no está activo' in str(response.data['errors']['customer'])
        
        print(f"✅ UT-SOL-003: APROBADO - Cliente inactivo rechazado correctamente")
    
    def test_ut_sol_004_past_start_date(self):
        """
        UT-SOL-004: Verificar validación de fecha de inicio en el pasado
        
        Validar que el sistema rechaza presolicitudes con fecha de inicio
        anterior a la fecha actual.
        """
        # Arrange
        payload = self._get_valid_payload()
        past_date = (timezone.now() - timedelta(days=1)).date()
        payload['scheduled_start_date'] = past_date.strftime("%Y-%m-%d")
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'scheduled_start_date' in response.data['errors']
        assert 'no puede ser anterior' in str(response.data['errors']['scheduled_start_date'])
        
        print(f"✅ UT-SOL-004: APROBADO - Fecha de inicio pasada rechazada")
    
    def test_ut_sol_005_end_date_before_start_date(self):
        """
        UT-SOL-005: Verificar validación de fecha de fin anterior a fecha de inicio
        
        Validar que la fecha de finalización no puede ser anterior a la fecha de inicio.
        """
        # Arrange
        payload = self._get_valid_payload()
        start_date = (timezone.now() + timedelta(days=10)).date()
        end_date = (timezone.now() + timedelta(days=5)).date()
        payload['scheduled_start_date'] = start_date.strftime("%Y-%m-%d")
        payload['scheduled_end_date'] = end_date.strftime("%Y-%m-%d")
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'scheduled_end_date' in response.data['errors']
        
        print(f"✅ UT-SOL-005: APROBADO - Fechas inconsistentes rechazadas")
    
    @patch('service_requests.api.service_request_viewset.requests.post')
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_006_date_conflict(self, mock_audit, mock_requests_post):
        """
        UT-SOL-006: Verificar detección de conflictos de fechas con solicitudes existentes
        
        Validar que el sistema detecta conflictos de fechas con solicitudes ya programadas.
        """
        # Arrange
        mock_requests_post.return_value = MagicMock(status_code=200)
        mock_audit.return_value.create = MagicMock()
        
        # Crear solicitud existente
        existing_start = (timezone.now() + timedelta(days=3)).date()
        existing_end = (timezone.now() + timedelta(days=4)).date()
        
        existing_request = ServiceRequest.objects.create(
            id_request='SOL-2025-0004',
            customer=self.customer,
            request_detail='Solicitud existente',
            scheduled_start_date=existing_start,
            scheduled_end_date=existing_end,
            request_status=self.status_pre_request,
            id_responsible_user=self.responsible_user
        )
        
        # Intentar crear solicitud con fechas solapadas
        payload = self._get_valid_payload()
        payload['scheduled_start_date'] = existing_start.strftime("%Y-%m-%d")
        payload['scheduled_end_date'] = (existing_end + timedelta(days=1)).strftime("%Y-%m-%d")
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'non_field_errors' in response.data['errors'] or 'errors' in response.data
        
        print(f"✅ UT-SOL-006: APROBADO - Conflicto de fechas detectado")
    
    def test_ut_sol_007_invalid_latitude(self):
        """
        UT-SOL-007: Verificar validación de formato de coordenadas de latitud
        
        Validar que el sistema rechaza latitudes con formato incorrecto o fuera de rango.
        """
        # Arrange
        payload = self._get_valid_payload()
        payload['location']['latitude'] = "95.123456"  # Fuera de rango
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'location' in response.data['errors']
        assert 'latitude' in response.data['errors']['location']
        
        print(f"✅ UT-SOL-007: APROBADO - Latitud inválida rechazada")
    
    def test_ut_sol_008_invalid_longitude(self):
        """
        UT-SOL-008: Verificar validación de formato de coordenadas de longitud
        
        Validar que el sistema rechaza longitudes con formato incorrecto o fuera de rango.
        """
        # Arrange
        payload = self._get_valid_payload()
        payload['location']['longitude'] = "190.123456"  # Fuera de rango
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'location' in response.data['errors']
        assert 'longitude' in response.data['errors']['location']
        
        print(f"✅ UT-SOL-008: APROBADO - Longitud inválida rechazada")
    
    def test_ut_sol_009_negative_area(self):
        """
        UT-SOL-009: Verificar validación de área negativa
        
        Validar que el sistema rechaza valores negativos para el área del terreno.
        """
        # Arrange
        payload = self._get_valid_payload()
        payload['location']['area'] = "-15.5"
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'location' in response.data['errors']
        assert 'area' in response.data['errors']['location']
        
        print(f"✅ UT-SOL-009: APROBADO - Área negativa rechazada")
    
    def test_ut_sol_010_invalid_humidity_level(self):
        """
        UT-SOL-010: Verificar validación de nivel de humedad fuera de rango
        
        Validar que el nivel de humedad debe estar entre 0 y 100%.
        """
        # Arrange
        payload = self._get_valid_payload()
        payload['location']['humidity_level'] = 150  # Fuera de rango
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'location' in response.data['errors']
        assert 'humidity_level' in response.data['errors']['location']
        
        print(f"✅ UT-SOL-010: APROBADO - Humedad fuera de rango rechazada")
    
    def test_ut_sol_011_missing_required_fields(self):
        """
        UT-SOL-011: Verificar validación de campos obligatorios faltantes
        
        Validar que el sistema rechaza solicitudes con campos obligatorios nulos o vacíos.
        """
        # Arrange
        payload = {
            "customer": None,
            "request_detail": None,
            "scheduled_start_date": None,
            "scheduled_end_date": None,
            "location": {
                "country": None,
                "department": None,
                "city_id": None,
                "place_name": None
            }
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'errors' in response.data
        
        print(f"✅ UT-SOL-011: APROBADO - Campos obligatorios validados")
    
    def test_ut_sol_012_max_length_validation(self):
        """
        UT-SOL-012: Verificar validación de longitud máxima de caracteres
        
        Validar que los campos respeten los límites de caracteres establecidos.
        """
        # Arrange
        payload = self._get_valid_payload()
        payload['request_detail'] = 'A' * 601  # Excede el límite de 600
        payload['location']['place_name'] = 'B' * 256  # Excede el límite de 255
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        
        print(f"✅ UT-SOL-012: APROBADO - Límites de caracteres validados")
    
    def test_ut_sol_013_unauthorized_access(self):
        """
        UT-SOL-013: Verificar acceso sin autenticación
        
        Validar que el endpoint rechaza solicitudes sin token de autenticación.
        """
        # Arrange
        payload = self._get_valid_payload()
        
        # Act - Sin autenticación
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 401
        
        print(f"✅ UT-SOL-013: APROBADO - Acceso no autenticado rechazado")
    
    def test_ut_sol_014_forbidden_access(self):
        """
        UT-SOL-014: Verificar acceso sin permisos
        
        Validar que usuarios sin el permiso 145 no pueden crear presolicitudes.
        """
        # Arrange
        payload = self._get_valid_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_without_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 403
        
        print(f"✅ UT-SOL-014: APROBADO - Acceso sin permisos rechazado")
    
    def test_ut_sol_015_invalid_area_unit_category(self):
        """
        UT-SOL-015: Verificar validación de categoría de unidad de área
        
        Validar que la unidad de área debe pertenecer a la categoría correcta (ID=11).
        """
        # Arrange
        wrong_unit = Units.objects.create(
            id_units=999,
            name="Unidad incorrecta",
            symbol="ui",
            id_units_categories=self.length_units_category,  # Categoría incorrecta
            id_types=self.length_type,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        payload = self._get_valid_payload()
        payload['location']['area_unit'] = wrong_unit.id_units
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        
        print(f"✅ UT-SOL-015: APROBADO - Categoría de unidad de área validada")
    
    def test_ut_sol_016_invalid_soil_type_category(self):
        """
        UT-SOL-016: Verificar validación de categoría de tipo de suelo
        
        Validar que el tipo de suelo debe pertenecer a la categoría correcta (ID=15).
        """
        # Arrange
        wrong_category = TypesCategory.objects.create(
            id_types_categories=999,
            name="Categoría incorrecta",
            description="Categoría de prueba",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        wrong_type = Types.objects.create(
            id_types=999,
            name="Tipo incorrecto",
            description="Tipo de prueba",
            id_types_categories=wrong_category,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        payload = self._get_valid_payload()
        payload['location']['soil_type'] = wrong_type.id_types
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        
        print(f"✅ UT-SOL-016: APROBADO - Categoría de tipo de suelo validada")
    
    def test_ut_sol_017_invalid_altitude_unit_category(self):
        """
        UT-SOL-017: Verificar validación de categoría de unidad de altitud
        
        Validar que la unidad de altitud debe pertenecer a la categoría correcta (ID=7).
        """
        # Arrange
        wrong_unit = Units.objects.create(
            id_units=998,
            name="Unidad incorrecta altitud",
            symbol="uia",
            id_units_categories=self.area_units_category,  # Categoría incorrecta
            id_types=self.area_type,
            id_statues=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        payload = self._get_valid_payload()
        payload['location']['altitude_unit'] = wrong_unit.id_units
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        
        print(f"✅ UT-SOL-017: APROBADO - Categoría de unidad de altitud validada")
    
    def test_ut_sol_018_negative_altitude(self):
        """
        UT-SOL-018: Verificar validación de altitud negativa
        
        Validar que el sistema rechaza valores negativos para la altitud.
        """
        # Arrange
        payload = self._get_valid_payload()
        payload['location']['altitude'] = -100
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert 'location' in response.data['errors']
        assert 'altitude' in response.data['errors']['location']
        
        print(f"✅ UT-SOL-018: APROBADO - Altitud negativa rechazada")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
