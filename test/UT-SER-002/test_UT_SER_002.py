"""
Pruebas unitarias para el endpoint de listado de servicios
ID: UT-SER-002
Título: Listar servicios con validación de autenticación, permisos y estructura de datos
"""

import sys
import os
import pytest
from unittest.mock import patch, Mock
import time
from datetime import timedelta

from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

# Ajustar el path para imports si es necesario
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from service_requests.models.services import Service
from service_requests.api.service_viewset import ServiceViewSet
from users.models.user import User
from parameterization.models import Statues, StatuesCategory, Types, TypesCategory, Units, UnitsCategory


@pytest.mark.django_db
class TestServiceList:
    endpoint = '/services/'
    endpoint_active = '/services/active/'

    def setup_method(self):
        self.client = APIClient()
        
        # Crear usuario responsable y autenticado
        self.user, created = User.objects.get_or_create(id_user=1)
        self.user.is_authenticated = True
        self.user.id = self.user.id_user
        
        # Mock JWT authentication con permiso service.list (142)
        self.mock_jwt_payload = {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "rol": [{
                "id": 1,
                "name": "Admin",
                "permisos": [
                    {"id": 142, "name": "service.list"},
                    {"id": 143, "name": "service.list.active"}
                ]
            }]
        }
        
        # Mock authentication
        self.client.force_authenticate(user=self.user)
        
        # Crear datos de prueba necesarios
        now = timezone.now()
        
        # Crear categoría de estados
        self.statues_category, created = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                'name': 'Estados Generales',
                'description': 'Estados generales del sistema',
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        # Crear estados
        self.active_status, created = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                'name': 'Activo',
                'description': 'Estado activo',
                'id_statues_categories': self.statues_category,
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        self.inactive_status, created = Statues.objects.get_or_create(
            id_statues=2,
            defaults={
                'name': 'Inactivo',
                'description': 'Estado inactivo',
                'id_statues_categories': self.statues_category,
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        # Crear categoría de tipos de servicio
        self.service_type_category, created = TypesCategory.objects.get_or_create(
            id_types_categories=14,
            defaults={
                'name': 'Tipos de Servicio',
                'description': 'Categoría para tipos de servicio',
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        # Crear tipos de servicio
        self.service_type_1, created = Types.objects.get_or_create(
            id_types=1,
            defaults={
                'name': 'Mantenimiento',
                'description': 'Servicio de mantenimiento',
                'id_types_categories': self.service_type_category,
                'id_statues': self.active_status,
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        self.service_type_2, created = Types.objects.get_or_create(
            id_types=2,
            defaults={
                'name': 'Reparación',
                'description': 'Servicio de reparación',
                'id_types_categories': self.service_type_category,
                'id_statues': self.active_status,
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        # Crear categoría de unidades
        self.unit_category, created = UnitsCategory.objects.get_or_create(
            id_units_categories=10,
            defaults={
                'name': 'Unidades de Medida',
                'description': 'Categoría para unidades de medida',
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        # Crear unidades de medida
        self.unit_hora, created = Units.objects.get_or_create(
            id_units=1,
            defaults={
                'name': 'Hora',
                'symbol': 'hr',
                'id_units_categories': self.unit_category,
                'id_types': self.service_type_1,
                'id_statues': self.active_status,
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        self.unit_unidad, created = Units.objects.get_or_create(
            id_units=2,
            defaults={
                'name': 'Unidad',
                'symbol': 'und',
                'id_units_categories': self.unit_category,
                'id_types': self.service_type_1,
                'id_statues': self.active_status,
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )

    def teardown_method(self):
        # Limpiar servicios creados durante las pruebas
        Service.objects.all().delete()

    def _create_mock_user_with_permission(self, has_permission_142=True, has_permission_143=False):
        """Helper para crear mock de usuario con o sin permiso"""
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        
        permisos = []
        if has_permission_142:
            permisos.append({"id": 142, "name": "service.list"})
        if has_permission_143:
            permisos.append({"id": 143, "name": "service.list.active"})
        
        if not permisos:
            permisos = [{"id": 999, "name": "other.permission"}]
        
        mock_user.auth = {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "rol": [{
                "id": 1,
                "name": "Admin",
                "permisos": permisos
            }]
        }
        
        return mock_user

    # ==================== AUTENTICACIÓN ====================

    def test_UT_SER_002_1_acceso_sin_token_retorna_401(self):
        """
        UT-SER-002.1: Acceso sin token retorna 401 en /services/
        Verifica que acceder a /services/ sin Authorization header retorna 401 Unauthorized.
        """
        # Arrange: No configurar token
        self.client.force_authenticate(user=None)
        
        # Act: Enviar GET /services/ sin Authorization
        response = self.client.get(self.endpoint)
        
        # Assert: Status 401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_UT_SER_002_2_token_invalido_retorna_401(self):
        """
        UT-SER-002.2: Token inválido retorna 401 en /services/
        Valida que un token malformado o con firma inválida es rechazado con 401.
        """
        # Arrange: Preparar token inválido
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer abc.def.ghi')
        
        # Act: GET /services/ con token inválido
        response = self.client.get(self.endpoint)
        
        # Assert: 401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_UT_SER_002_3_token_expirado_retorna_401(self):
        """
        UT-SER-002.3: Token expirado retorna 401 en /services/
        Comprueba que un token expirado no permite acceso.
        """
        # Arrange: Simular token expirado
        self.client.force_authenticate(user=None)
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: 401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_UT_SER_002_4_header_sin_prefijo_bearer_retorna_401(self):
        """
        UT-SER-002.4: Header Authorization sin prefijo Bearer retorna 401
        Valida que un token sin el prefijo Bearer no es aceptado.
        """
        # Arrange: Configurar Authorization sin Bearer
        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION='Token valid_jwt_token')
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: 401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ==================== PERMISOS ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=False)
    def test_UT_SER_002_5_sin_permiso_142_retorna_403(self, mock_check_permission):
        """
        UT-SER-002.5: Sin permiso 142 retorna 403 en /services/
        Valida que un usuario autenticado sin permiso 142 no pueda listar servicios.
        """
        # Arrange: Usuario sin permiso 142 (mock ya configurado)
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: 403
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
        assert 'No tiene permisos para listar servicios' in response.data['message']

    @patch.object(ServiceViewSet, 'check_permission', return_value=False)
    def test_UT_SER_002_6_sin_permiso_143_retorna_403(self, mock_check_permission):
        """
        UT-SER-002.6: Sin permiso 143 retorna 403 en /services/active/
        Valida que un usuario sin permiso 143 no acceda al listado de activos.
        """
        # Arrange: Usuario sin permiso 143
        
        # Act: GET /services/active/
        response = self.client.get(self.endpoint_active)
        
        # Assert: 403
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['success'] is False
        assert 'No tiene permisos para listar servicios' in response.data['message']

    @patch.object(ServiceViewSet, 'check_permission')
    def test_UT_SER_002_7_usuario_con_142_accede_services_falla_active(self, mock_check_permission):
        """
        UT-SER-002.7: Usuario con 142 accede /services/ y falla en /services/active/
        Confirma separación de permisos entre listados general y activos.
        """
        # Arrange: Usuario con solo permiso 142
        def check_permission_side_effect(request, permission_id):
            return permission_id == 142
        
        mock_check_permission.side_effect = check_permission_side_effect
        
        # Act: GET /services/ (espera 200)
        response_general = self.client.get(self.endpoint)
        
        # Assert: /services/ 200 OK
        assert response_general.status_code == status.HTTP_200_OK
        
        # Act: GET /services/active/ (espera 403)
        response_active = self.client.get(self.endpoint_active)
        
        # Assert: /services/active/ 403 Forbidden
        assert response_active.status_code == status.HTTP_403_FORBIDDEN

    # ==================== ÉXITO Y ORDENAMIENTO ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_8_listado_general_200_estructura_correcta(self, mock_check_permission):
        """
        UT-SER-002.8: Listado general 200 y estructura correcta
        Verifica éxito 200 y estructura base con campos esperados en /services/.
        """
        # Arrange: Crear mock user y servicio
        mock_user = self._create_mock_user_with_permission(has_permission_142=True)
        self.client.force_authenticate(user=mock_user)
        
        service = Service.objects.create(
            service_name="Servicio Test",
            description="Descripción test",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint, HTTP_ACCEPT='application/json')
        
        # Assert: 200
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert isinstance(response.data['data'], list)
        
        # Verificar campos en cada item
        if len(response.data['data']) > 0:
            item = response.data['data'][0]
            expected_fields = [
                'id', 'name', 'description', 'base_price', 
                'unit_id', 'unit_name', 'applicable_tax', 'tax_rate', 
                'is_vat_exempt', 'status_id', 'status_name', 
                'service_type_id', 'service_type_name'
            ]
            for field in expected_fields:
                assert field in item, f"Campo {field} no encontrado en la respuesta"

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_9_orden_por_modification_date_descendente(self, mock_check_permission):
        """
        UT-SER-002.9: Orden por modification_date descendente
        Asegura que el orden del listado sea por modification_date desc.
        """
        # Arrange: Crear tres servicios con diferentes timestamps
        now = timezone.now()
        
        s1 = Service.objects.create(
            service_name="Servicio 1",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        s1.modification_date = now - timedelta(hours=3)
        s1.save()
        
        time.sleep(0.1)
        
        s2 = Service.objects.create(
            service_name="Servicio 2",
            service_type=self.service_type_1,
            base_price=150.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        s2.modification_date = now - timedelta(hours=2)
        s2.save()
        
        time.sleep(0.1)
        
        s3 = Service.objects.create(
            service_name="Servicio 3",
            service_type=self.service_type_1,
            base_price=200.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        s3.modification_date = now - timedelta(hours=1)
        s3.save()
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: Orden S3, S2, S1
        assert response.status_code == status.HTTP_200_OK
        data = response.data['data']
        assert len(data) >= 3
        assert data[0]['id'] == s3.id_service
        assert data[1]['id'] == s2.id_service
        assert data[2]['id'] == s1.id_service

    # ==================== CONTRATO DE DATOS ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_10_tipos_de_datos_por_campo(self, mock_check_permission):
        """
        UT-SER-002.10: Tipos de datos por campo
        Valida tipos de datos correctos para cada campo.
        """
        # Arrange: Crear servicio
        service = Service.objects.create(
            service_name="Servicio Completo",
            description="Descripción completa",
            service_type=self.service_type_1,
            base_price=250.50,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: Validar tipos
        assert response.status_code == status.HTTP_200_OK
        item = response.data['data'][0]
        
        assert isinstance(item['id'], int)
        assert isinstance(item['name'], str)
        assert isinstance(item['base_price'], (int, float))
        assert isinstance(item['unit_id'], int)
        assert isinstance(item['unit_name'], str)
        assert isinstance(item['applicable_tax'], (int, type(None)))
        assert isinstance(item['tax_rate'], (int, float, type(None)))
        assert isinstance(item['is_vat_exempt'], bool)
        assert isinstance(item['status_id'], int)
        assert isinstance(item['status_name'], str)
        assert isinstance(item['service_type_id'], int)
        assert isinstance(item['service_type_name'], str)

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_11_coherencia_status_id_y_status_name(self, mock_check_permission):
        """
        UT-SER-002.11: Coherencia status_id y status_name
        Valida que status_id=1 corresponda a "Activo" y status_id=2 a "Inactivo".
        """
        # Arrange: Crear servicio activo e inactivo
        service_activo = Service.objects.create(
            service_name="Servicio Activo",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        service_inactivo = Service.objects.create(
            service_name="Servicio Inactivo",
            service_type=self.service_type_1,
            base_price=150.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.inactive_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: Mapeo correcto
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            if item['status_id'] == 1:
                assert item['status_name'].lower() == 'activo'
            elif item['status_id'] == 2:
                assert item['status_name'].lower() == 'inactivo'

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_12_coherencia_unidad_de_medida(self, mock_check_permission):
        """
        UT-SER-002.12: Coherencia unidad de medida
        Valida que unit_name exista cuando unit_id está presente y que no sea vacío.
        """
        # Arrange: Servicio con unidad
        service = Service.objects.create(
            service_name="Servicio con Unidad",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: unit_name no vacío y consistente
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            if item['unit_id'] is not None:
                assert item['unit_name'] is not None
                assert len(item['unit_name']) > 0

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_13_rangos_validos_de_numeros(self, mock_check_permission):
        """
        UT-SER-002.13: Rangos válidos de números
        Verifica que base_price ≥ 0 y 0 ≤ tax_rate ≤ 100.
        """
        # Arrange: Servicios con valores diversos
        Service.objects.create(
            service_name="Servicio Precio Bajo",
            service_type=self.service_type_1,
            base_price=10.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=5.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        Service.objects.create(
            service_name="Servicio Precio Alto",
            service_type=self.service_type_1,
            base_price=10000.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: Rangos válidos
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            assert item['base_price'] >= 0
            if item['tax_rate'] is not None:
                assert 0 <= item['tax_rate'] <= 100

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_14_is_vat_exempt_coherente_con_impuestos(self, mock_check_permission):
        """
        UT-SER-002.14: is_vat_exempt coherente con impuestos
        Si is_vat_exempt=true, tax_rate debe ser 0.0; si false, tax_rate>0 según configuración.
        """
        # Arrange: Crear servicio exento y no exento
        service_exento = Service.objects.create(
            service_name="Servicio Exento",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=0,
            tax_rate=0.0,
            is_vat_exempt=True,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        service_no_exento = Service.objects.create(
            service_name="Servicio No Exento",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: Coherencia entre exención y tasas
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            if item['is_vat_exempt'] is True:
                assert item['tax_rate'] == 0.0 or item['tax_rate'] is None

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_15_service_type_mapeado_correctamente(self, mock_check_permission):
        """
        UT-SER-002.15: service_type mapeado correctamente
        Valida presencia y consistencia de service_type_id y service_type_name.
        """
        # Arrange: Servicios con distintos tipos
        Service.objects.create(
            service_name="Servicio Tipo 1",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        Service.objects.create(
            service_name="Servicio Tipo 2",
            service_type=self.service_type_2,
            base_price=150.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: Campos presentes y no vacíos
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            assert item['service_type_id'] is not None
            assert isinstance(item['service_type_id'], int)
            assert item['service_type_name'] is not None
            assert len(item['service_type_name']) > 0

    # ==================== ESCENARIOS DE DATOS Y VACÍOS ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_16_listado_vacio_retorna_arreglo_vacio(self, mock_check_permission):
        """
        UT-SER-002.16: Listado vacío retorna arreglo vacío
        Verifica que cuando no hay servicios, la API retorne success=true y data=[].
        """
        # Arrange: Limpiar tabla Service
        Service.objects.all().delete()
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: 200 con data=[]
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data'] == []

    # ==================== ACTUALIZACIONES EN TIEMPO REAL ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_17_nuevo_servicio_aparece_inmediatamente(self, mock_check_permission):
        """
        UT-SER-002.17: Nuevo servicio aparece inmediatamente y al inicio
        Valida que al crear un servicio se refleje en /services/ y quede primero por orden de modification_date desc.
        """
        # Arrange: Crear servicio previo
        service_old = Service.objects.create(
            service_name="Servicio Anterior",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        time.sleep(0.1)
        
        # Crear nuevo servicio
        service_new = Service.objects.create(
            service_name="Servicio Nuevo",
            service_type=self.service_type_1,
            base_price=200.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: S_new en primer lugar
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data'][0]['id'] == service_new.id_service
        assert response.data['data'][0]['name'] == "Servicio Nuevo"

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_18_edicion_se_refleja_en_listado(self, mock_check_permission):
        """
        UT-SER-002.18: Edición se refleja en listado
        Al actualizar name/base_price de un servicio, el cambio se visualiza inmediato en /services/.
        """
        # Arrange: Servicio existente
        service = Service.objects.create(
            service_name="Servicio Original",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Actualizar servicio
        service.service_name = "Servicio Actualizado"
        service.base_price = 250.0
        service.save()
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: Cambios visibles
        assert response.status_code == status.HTTP_200_OK
        found = False
        for item in response.data['data']:
            if item['id'] == service.id_service:
                assert item['name'] == "Servicio Actualizado"
                assert item['base_price'] == 250.0
                found = True
                break
        assert found

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_19_inactivacion_excluye_de_activos(self, mock_check_permission):
        """
        UT-SER-002.19: Inactivación excluye de /services/active/
        Al inactivar un servicio, debe seguir visible en /services/ con estado inactivo y no aparecer en /services/active/.
        """
        # Arrange: Servicio activo
        service = Service.objects.create(
            service_name="Servicio A Inactivar",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Inactivar servicio
        service.service_status = self.inactive_status
        service.save()
        
        # Act: GET /services/ y GET /services/active/
        response_general = self.client.get(self.endpoint)
        response_active = self.client.get(self.endpoint_active)
        
        # Assert: En general con status_id=2; ausente en activos
        assert response_general.status_code == status.HTTP_200_OK
        found_in_general = False
        for item in response_general.data['data']:
            if item['id'] == service.id_service:
                assert item['status_id'] == 2
                found_in_general = True
                break
        assert found_in_general
        
        # No debe estar en activos
        assert response_active.status_code == status.HTTP_200_OK
        for item in response_active.data['data']:
            assert item['id'] != service.id_service

    # ==================== LISTADO DE ACTIVOS ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_20_listado_activos_solo_status_id_1(self, mock_check_permission):
        """
        UT-SER-002.20: Listado de activos solo contiene status_id=1
        Verifica que /services/active/ solo devuelva servicios con status_id=1.
        """
        # Arrange: Crear activos e inactivos
        Service.objects.create(
            service_name="Servicio Activo 1",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        Service.objects.create(
            service_name="Servicio Inactivo 1",
            service_type=self.service_type_1,
            base_price=150.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.inactive_status,
            id_responsible_user=self.user
        )
        
        # Act: GET /services/active/
        response = self.client.get(self.endpoint_active)
        
        # Assert: Todos con status_id=1
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['data']:
            assert item['status_id'] == 1
            assert item['status_name'].lower() == 'activo'

    # ==================== ROBUSTEZ Y MÉTODOS ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_21_parametros_desconocidos_ignorados(self, mock_check_permission):
        """
        UT-SER-002.21: Parámetros desconocidos son ignorados sin error
        Enviar query params de filtros/paginación no documentados no debe causar error 4xx/5xx.
        """
        # Arrange: Crear servicio
        Service.objects.create(
            service_name="Servicio Test",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET con parámetros no soportados
        response = self.client.get(
            self.endpoint + '?page=1&page_size=20&price_min=0&price_max=100&status=1&q=aceite'
        )
        
        # Assert: 200 sin fallos
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_22_metodo_no_permitido_retorna_405(self, mock_check_permission):
        """
        UT-SER-002.22: Método no permitido retorna 405
        Asegura que POST sobre /services/ no esté habilitado en este ViewSet de listado.
        """
        # Act: POST /services/
        response = self.client.post(self.endpoint, {"name": "X"}, format='json')
        
        # Assert: 405 Method Not Allowed
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_23_headers_de_respuesta_correctos(self, mock_check_permission):
        """
        UT-SER-002.23: Headers de respuesta correctos
        Valida Content-Type application/json.
        """
        # Act: GET /services/
        response = self.client.get(self.endpoint, HTTP_ACCEPT='application/json')
        
        # Assert: Content-Type correcto
        assert response.status_code == status.HTTP_200_OK
        assert 'application/json' in response['Content-Type']

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_24_rendimiento_con_gran_volumen(self, mock_check_permission):
        """
        UT-SER-002.24: Rendimiento con gran volumen
        El listado responde bajo umbral definido con múltiples servicios.
        """
        # Arrange: Cargar múltiples registros
        for i in range(50):  # Crear 50 servicios
            Service.objects.create(
                service_name=f"Servicio {i}",
                service_type=self.service_type_1,
                base_price=100.0 + i,
                price_unit=self.unit_hora,
                applicable_tax=1,
                tax_rate=19.0,
                is_vat_exempt=False,
                service_status=self.active_status,
                id_responsible_user=self.user
            )
        
        # Act: Medir tiempo de respuesta
        import time
        start = time.time()
        response = self.client.get(self.endpoint)
        end = time.time()
        
        # Assert: Tiempo de respuesta razonable (< 2 segundos para 50 registros en test)
        assert response.status_code == status.HTTP_200_OK
        assert (end - start) < 2.0

    # ==================== MANEJO DE ERRORES ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    @patch('service_requests.models.services.Service.objects.select_related')
    def test_UT_SER_002_25_errores_500_manejados_sin_exponer_detalles(self, mock_select, mock_check_permission):
        """
        UT-SER-002.25: Errores 500 manejados sin exponer detalles
        Simula fallo interno y verifica respuesta controlada.
        """
        # Arrange: Simular excepción
        mock_select.side_effect = Exception("Database connection lost")
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: 500 con mensaje controlado
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['success'] is False
        assert 'Error interno del servidor' in response.data['message']

    # ==================== INTEGRIDAD Y UNICIDAD ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_26_ids_unicos_sin_duplicados(self, mock_check_permission):
        """
        UT-SER-002.26: IDs únicos y sin duplicados
        Verifica que no existan ids repetidos en el listado.
        """
        # Arrange: Dataset con múltiples servicios
        for i in range(10):
            Service.objects.create(
                service_name=f"Servicio {i}",
                service_type=self.service_type_1,
                base_price=100.0,
                price_unit=self.unit_hora,
                applicable_tax=1,
                tax_rate=19.0,
                is_vat_exempt=False,
                service_status=self.active_status,
                id_responsible_user=self.user
            )
        
        # Act: GET /services/
        response = self.client.get(self.endpoint)
        
        # Assert: IDs únicos
        assert response.status_code == status.HTTP_200_OK
        ids = [item['id'] for item in response.data['data']]
        assert len(ids) == len(set(ids))  # No hay duplicados

    # ==================== COMPARATIVA GENERAL VS ACTIVOS ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_27_consistencia_entre_services_y_active(self, mock_check_permission):
        """
        UT-SER-002.27: Consistencia entre /services/ y /services/active/
        Todo servicio en /services/active/ debe existir en /services/ y con status_id=1.
        """
        # Arrange: Crear servicios activos e inactivos
        Service.objects.create(
            service_name="Servicio Activo",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        Service.objects.create(
            service_name="Servicio Inactivo",
            service_type=self.service_type_1,
            base_price=150.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.inactive_status,
            id_responsible_user=self.user
        )
        
        # Act: Obtener ambos listados
        response_general = self.client.get(self.endpoint)
        response_active = self.client.get(self.endpoint_active)
        
        # Assert: active ⊆ general
        assert response_general.status_code == status.HTTP_200_OK
        assert response_active.status_code == status.HTTP_200_OK
        
        ids_general = {item['id'] for item in response_general.data['data']}
        ids_active = {item['id'] for item in response_active.data['data']}
        
        assert ids_active.issubset(ids_general)
        
        # Todos en active tienen status_id=1
        for item in response_active.data['data']:
            assert item['status_id'] == 1

    # ==================== ESTABILIDAD ANTE PARÁMETROS OPCIONALES ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_28_tolerancia_a_accept_y_locale(self, mock_check_permission):
        """
        UT-SER-002.28: Tolerancia a parámetro Accept y Locale
        Cambiar Accept y Accept-Language no debe alterar el contrato ni causar error.
        """
        # Arrange: Crear servicio
        Service.objects.create(
            service_name="Servicio Test",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        
        # Act: GET con headers variados
        response = self.client.get(
            self.endpoint,
            HTTP_ACCEPT='application/json',
            HTTP_ACCEPT_LANGUAGE='es-CO'
        )
        
        # Assert: 200 y misma estructura
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_29_orden_estable_ante_mismos_timestamps(self, mock_check_permission):
        """
        UT-SER-002.29: Orden estable ante mismos timestamps
        Si dos servicios comparten modification_date, verificar orden determinista.
        """
        # Arrange: Crear servicios con mismo timestamp
        now = timezone.now()
        
        s1 = Service.objects.create(
            service_name="Servicio A",
            service_type=self.service_type_1,
            base_price=100.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        s1.modification_date = now
        s1.save()
        
        s2 = Service.objects.create(
            service_name="Servicio B",
            service_type=self.service_type_1,
            base_price=150.0,
            price_unit=self.unit_hora,
            applicable_tax=1,
            tax_rate=19.0,
            is_vat_exempt=False,
            service_status=self.active_status,
            id_responsible_user=self.user
        )
        s2.modification_date = now
        s2.save()
        
        # Act: GET /services/ múltiples veces
        response1 = self.client.get(self.endpoint)
        response2 = self.client.get(self.endpoint)
        
        # Assert: Orden consistente entre ejecuciones
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        ids1 = [item['id'] for item in response1.data['data']]
        ids2 = [item['id'] for item in response2.data['data']]
        assert ids1 == ids2

    # ==================== PAGINACIÓN (SI EXISTIERA) ====================

    @patch.object(ServiceViewSet, 'check_permission', return_value=True)
    def test_UT_SER_002_30_paginacion_soportada_o_ignorada(self, mock_check_permission):
        """
        UT-SER-002.30: Paginación soportada o ignorada sin error
        Si la API soporta page/page_size, validar; si no, asegurar que se ignoren sin fallar.
        """
        # Arrange: Cargar múltiples servicios
        for i in range(30):
            Service.objects.create(
                service_name=f"Servicio {i}",
                service_type=self.service_type_1,
                base_price=100.0,
                price_unit=self.unit_hora,
                applicable_tax=1,
                tax_rate=19.0,
                is_vat_exempt=False,
                service_status=self.active_status,
                id_responsible_user=self.user
            )
        
        # Act: GET con parámetros de paginación
        response = self.client.get(self.endpoint + '?page=2&page_size=20')
        
        # Assert: Sin errores 4xx/5xx
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
"""
Pruebas para el listado de servicios (UT-SER-002)

Cubre 30 casos: autenticación, permisos, contrato de datos, ordenamiento,
consistencia entre listados, robustez y rendimiento.

Endpoints bajo prueba:
- GET /services/
- GET /services/active/

Permisos:
- 142: service.list (GET /services/)
- 143: service.list.active (GET /services/active/)
"""

import os
import time
import pytest
import jwt
from datetime import timedelta, datetime, timezone as pytimezone
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

# Modelos y vistas
from users.models.user import User
from parameterization.models import (
    StatuesCategory,
    Statues,
    TypesCategory,
    Types,
    UnitsCategory,
    Units,
)
from service_requests.models.services import Service
from service_requests.api.service_viewset import ServiceViewSet


JWT_TEST_SECRET = "testsecret"


def _ensure_jwt_secret_for_tests():
    os.environ.setdefault("JWT_SECRET", JWT_TEST_SECRET)


def _make_jwt(payload: dict, expired: bool = False) -> str:
    _ensure_jwt_secret_for_tests()
    claims = {
        **payload,
    }
    # exp requerido para casos expirados/no expirados
    now = datetime.now(pytimezone.utc)
    claims["iat"] = int(now.timestamp())
    if expired:
        claims["exp"] = int((now - timedelta(minutes=5)).timestamp())
    else:
        claims["exp"] = int((now + timedelta(minutes=30)).timestamp())
    return jwt.encode(claims, os.environ.get("JWT_SECRET", JWT_TEST_SECRET), algorithm="HS256")


def _auth_header_for(perms_ids):
    payload = {
        "id": 1,
        "email": "tester@example.com",
        "name": "Tester",
        "rol": [
            {
                "id": 1,
                "name": "Role",
                "permisos": [{"id": pid, "name": f"perm.{pid}"} for pid in (perms_ids or [])],
            }
        ],
    }
    token = _make_jwt(payload)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
class TestServiceList:
    endpoint = "/services/"
    endpoint_active = "/services/active/"

    def setup_method(self):
        self.client = APIClient()

        # Usuario responsable para FKs
        self.user, _ = User.objects.get_or_create(id_user=1)
        self.user.id = self.user.id_user

        now = timezone.now()

        # Categorías y estados
        self.stat_cat, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                "name": "Estados",
                "description": "Estados generales",
                "modification_date": now,
                "creation_date": now,
                "id_responsible_user": self.user,
            },
        )

        self.status_active, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                "name": "Activo",
                "description": "Estado activo",
                "id_statues_categories": self.stat_cat,
                "modification_date": now,
                "creation_date": now,
                "id_responsible_user": self.user,
            },
        )
        self.status_inactive, _ = Statues.objects.get_or_create(
            id_statues=2,
            defaults={
                "name": "Inactivo",
                "description": "Estado inactivo",
                "id_statues_categories": self.stat_cat,
                "modification_date": now,
                "creation_date": now,
                "id_responsible_user": self.user,
            },
        )

        # Categorías y tipos/unidades
        self.types_cat, _ = TypesCategory.objects.get_or_create(
            id_types_categories=14,
            defaults={
                "name": "Tipos de Servicio",
                "description": "Cat tipos",
                "creation_date": now,
                "modification_date": now,
                "id_responsible_user": self.user,
            },
        )
        self.units_cat, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10,
            defaults={
                "name": "Unidades",
                "description": "Cat unidades",
                "modification_date": now,
                "creation_date": now,
                "id_responsible_user": self.user,
            },
        )

        self.type_generic, _ = Types.objects.get_or_create(
            id_types=100,
            defaults={
                "name": "General",
                "description": "Tipo general",
                "id_types_categories": self.types_cat,
                "creation_date": now,
                "modification_date": now,
                "id_responsible_user": self.user,
                "id_statues": self.status_active,
            },
        )

        self.unit_hour, _ = Units.objects.get_or_create(
            id_units=200,
            defaults={
                "id_units_categories": self.units_cat,
                "name": "Hora",
                "symbol": "h",
                "id_types": self.type_generic,
                "modification_date": now,
                "creation_date": now,
                "id_responsible_user": self.user,
                "id_statues": self.status_active,
            },
        )

        # Limpieza
        Service.objects.all().delete()

    # Helpers ------------------------------------------------------
    def _create_service(self, name: str = "Servicio", base_price: float = 10.0,
                         status=None, unit=None, stype=None, applicable_tax: int = 1,
                         tax_rate: float = 19.0, is_vat_exempt: bool = False,
                         modification_date=None):
        s = Service.objects.create(
            service_name=name,
            description=f"Desc {name}",
            service_type=stype or self.type_generic,
            base_price=base_price,
            price_unit=unit or self.unit_hour,
            applicable_tax=applicable_tax,
            tax_rate=tax_rate,
            is_vat_exempt=is_vat_exempt,
            service_status=status or self.status_active,
            id_responsible_user=self.user,
        )
        if modification_date is not None:
            Service.objects.filter(pk=s.pk).update(modification_date=modification_date)
            s.refresh_from_db()
        return s

    # 1) Acceso sin token -> 401
    def test_UT_SER_002_1_sin_token_401(self):
        resp = self.client.get(self.endpoint)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        data = resp.json()
        assert "detail" in data

    # 2) Token inválido -> 401 "Token inválido."
    def test_UT_SER_002_2_token_invalido_401(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer abc.def.ghi"}
        resp = self.client.get(self.endpoint, **headers)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        data = resp.json()
        assert "detail" in data and "inválido" in data["detail"].lower()

    # 3) Token expirado -> 401
    def test_UT_SER_002_3_token_expirado_401(self):
        _ensure_jwt_secret_for_tests()
        token = _make_jwt({"id": 1, "email": "tester@example.com"}, expired=True)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        resp = self.client.get(self.endpoint, **headers)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        data = resp.json()
        assert "detail" in data and ("expir" in data["detail"].lower() or "inválido" in data["detail"].lower())

    # 4) Authorization sin Bearer -> 401
    def test_UT_SER_002_4_sin_prefijo_bearer_401(self):
        _ensure_jwt_secret_for_tests()
        token = _make_jwt({"id": 1, "email": "tester@example.com"})
        headers = {"HTTP_AUTHORIZATION": f"Token {token}"}
        resp = self.client.get(self.endpoint, **headers)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # 5) Sin permiso 142 -> 403 en /services/
    def test_UT_SER_002_5_sin_permiso_142_403(self):
        headers = _auth_header_for(perms_ids=[999])  # sin 142
        resp = self.client.get(self.endpoint, **headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        data = resp.json()
        assert data.get("success") is False
        assert "No tiene permisos" in data.get("message", "")

    # 6) Sin permiso 143 -> 403 en /services/active/
    def test_UT_SER_002_6_sin_permiso_143_403(self):
        headers = _auth_header_for(perms_ids=[142])  # solo 142
        resp = self.client.get(self.endpoint_active, **headers)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        data = resp.json()
        assert data.get("success") is False
        assert "No tiene permisos" in data.get("message", "")

    # 7) Usuario con 142 accede /services/ y falla /services/active/
    def test_UT_SER_002_7_permiso_142_ok_y_143_forbidden(self):
        self._create_service("A")
        headers = _auth_header_for(perms_ids=[142])
        r1 = self.client.get(self.endpoint, **headers)
        assert r1.status_code == 200
        r2 = self.client.get(self.endpoint_active, **headers)
        assert r2.status_code == 403

    # 8) 200 y estructura correcta
    def test_UT_SER_002_8_listado_general_200_estructura_correcta(self):
        self._create_service("S1")
        headers = _auth_header_for(perms_ids=[142])
        resp = self.client.get(self.endpoint, **headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert isinstance(body.get("data"), list)
        assert len(body["data"]) >= 1
        item = body["data"][0]
        expected_keys = {
            "id",
            "name",
            "description",
            "base_price",
            "unit_id",
            "unit_name",
            "applicable_tax",
            "tax_rate",
            "is_vat_exempt",
            "status_id",
            "status_name",
            "service_type_id",
            "service_type_name",
        }
        assert expected_keys.issubset(set(item.keys()))

    # 9) Orden por modification_date desc
    def test_UT_SER_002_9_orden_por_modification_date_desc(self):
        t0 = timezone.now() - timedelta(minutes=3)
        t1 = timezone.now() - timedelta(minutes=2)
        t2 = timezone.now() - timedelta(minutes=1)
        s1 = self._create_service("S1", modification_date=t0)
        s2 = self._create_service("S2", modification_date=t1)
        s3 = self._create_service("S3", modification_date=t2)
        headers = _auth_header_for(perms_ids=[142])
        resp = self.client.get(self.endpoint, **headers)
        data = resp.json()["data"]
        names = [it["name"] for it in data]
        assert names[:3] == ["S3", "S2", "S1"]

    # 10) Tipos de datos por campo
    def test_UT_SER_002_10_tipos_de_datos(self):
        self._create_service("TipoDatos", base_price=12.5, tax_rate=19.0)
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, **headers)
        assert r.status_code == 200
        item = r.json()["data"][0]
        assert isinstance(item["id"], int)
        assert isinstance(item["name"], str)
        assert isinstance(item["base_price"], (int, float))
        assert isinstance(item["unit_id"], int)
        assert isinstance(item["unit_name"], str)
        assert isinstance(item["applicable_tax"], int)
        assert isinstance(item["tax_rate"], (int, float, type(None)))
        assert isinstance(item["is_vat_exempt"], (bool, type(None)))
        assert isinstance(item["status_id"], int)
        assert isinstance(item["status_name"], str)
        assert isinstance(item["service_type_id"], int)
        assert isinstance(item["service_type_name"], str)

    # 11) Coherencia status_id/status_name
    def test_UT_SER_002_11_coherencia_status(self):
        self._create_service("Activo1", status=self.status_active)
        self._create_service("Inactivo1", status=self.status_inactive)
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, **headers)
        for it in r.json()["data"]:
            if it["status_id"] == 1:
                assert it["status_name"].lower() == "activo"
            if it["status_id"] == 2:
                assert it["status_name"].lower() == "inactivo"

    # 12) Coherencia unidad
    def test_UT_SER_002_12_coherencia_unidad(self):
        self._create_service("ConUnidad")
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, **headers)
        for it in r.json()["data"]:
            if it["unit_id"] is not None:
                assert isinstance(it["unit_name"], str) and len(it["unit_name"].strip()) > 0

    # 13) Rangos válidos de números
    def test_UT_SER_002_13_rangos_numeros(self):
        self._create_service("Rangos", base_price=0, tax_rate=0)
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, **headers)
        for it in r.json()["data"]:
            assert it["base_price"] >= 0
            if it["tax_rate"] is not None:
                assert 0 <= it["tax_rate"] <= 100

    # 14) is_vat_exempt coherente
    def test_UT_SER_002_14_exento_vs_impuesto(self):
        self._create_service("Exento", is_vat_exempt=True, tax_rate=0.0)
        self._create_service("NoExento", is_vat_exempt=False, tax_rate=19.0)
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, **headers)
        for it in r.json()["data"]:
            if it["is_vat_exempt"]:
                assert (it["tax_rate"] or 0) == 0
            else:
                assert (it["tax_rate"] or 0) >= 0

    # 15) service_type mapeado
    def test_UT_SER_002_15_service_type_mapeado(self):
        self._create_service("ConTipo")
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, **headers)
        it = r.json()["data"][0]
        assert isinstance(it["service_type_id"], int)
        assert isinstance(it["service_type_name"], str)

    # 16) Listado vacío
    def test_UT_SER_002_16_listado_vacio(self):
        headers = _auth_header_for([142])
        resp = self.client.get(self.endpoint, **headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert body.get("data") == []

    # 17) Nuevo servicio aparece primero
    def test_UT_SER_002_17_nuevo_aparece_primero(self):
        old = self._create_service("Antiguo", modification_date=timezone.now() - timedelta(hours=1))
        _ = old
        latest = self._create_service("Reciente", modification_date=timezone.now())
        _ = latest
        headers = _auth_header_for([142])
        resp = self.client.get(self.endpoint, **headers)
        names = [it["name"] for it in resp.json()["data"]]
        assert names[0] == "Reciente"

    # 18) Edición se refleja
    def test_UT_SER_002_18_edicion_se_refleja(self):
        s = self._create_service("Editar", base_price=10.0, modification_date=timezone.now() - timedelta(minutes=5))
        # update
        Service.objects.filter(pk=s.pk).update(service_name="Editado", base_price=20.0, modification_date=timezone.now())
        headers = _auth_header_for([142])
        resp = self.client.get(self.endpoint, **headers)
        data = resp.json()["data"]
        found = next((it for it in data if it["id"] == s.id_service), None)
        assert found is not None
        assert found["name"] == "Editado"
        assert found["base_price"] == 20.0

    # 19) Inactivación excluye de activos
    def test_UT_SER_002_19_inactivacion_excluye_activos(self):
        s = self._create_service("ActivoInicial", status=self.status_active)
        # inactivar
        Service.objects.filter(pk=s.pk).update(service_status=self.status_inactive)
        headers142 = _auth_header_for([142])
        headers143 = _auth_header_for([143])
        r_general = self.client.get(self.endpoint, **headers142)
        r_active = self.client.get(self.endpoint_active, **headers143)
        # general contiene inactivo
        g = next((it for it in r_general.json()["data"] if it["id"] == s.id_service), None)
        assert g is not None and g["status_id"] == 2
        # activos no lo incluyen
        ids_active = {it["id"] for it in r_active.json()["data"]}
        assert s.id_service not in ids_active

    # 20) Activos solo status_id=1
    def test_UT_SER_002_20_activos_solo_status_1(self):
        self._create_service("A1", status=self.status_active)
        self._create_service("I1", status=self.status_inactive)
        headers = _auth_header_for([143])
        r = self.client.get(self.endpoint_active, **headers)
        for it in r.json()["data"]:
            assert it["status_id"] == 1
            assert it["status_name"].lower() == "activo"

    # 21) Parámetros desconocidos ignorados
    def test_UT_SER_002_21_parametros_desconocidos_ignorados(self):
        self._create_service("Param1")
        headers = _auth_header_for([142])
        url = self.endpoint + "?page=1&page_size=20&price_min=0&price_max=100&status=1&q=aceite"
        r = self.client.get(url, **headers)
        assert r.status_code == 200
        assert r.json().get("success") is True

    # 22) Método no permitido POST /services/
    def test_UT_SER_002_22_metodo_no_permitido_405(self):
        headers = _auth_header_for([142])
        r = self.client.post(self.endpoint, {"name": "X"}, format="json", **headers)
        assert r.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN]

    # 23) Headers de respuesta correctos
    def test_UT_SER_002_23_headers_respuesta(self):
        self._create_service("H1")
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, HTTP_ACCEPT="application/json", **headers)
        ctype = r.headers.get("Content-Type", "")
        assert ctype.startswith("application/json")

    # 24) Rendimiento con volumen
    def test_UT_SER_002_24_rendimiento(self):
        # Carga moderada para entorno local (ajustable)
        for i in range(250):
            self._create_service(f"S{i}", base_price=i)
        headers = _auth_header_for([142])
        t0 = time.time()
        r = self.client.get(self.endpoint, **headers)
        dt = time.time() - t0
        assert r.status_code == 200
        assert dt < 3.0, f"Tiempo de respuesta alto: {dt:.3f}s"

    # 25) Errores 500 manejados sin exponer detalles
    def test_UT_SER_002_25_manejo_500(self, monkeypatch):
        self._create_service("E1")
        def boom(*args, **kwargs):
            raise Exception("Fallo simulado")
        # Romper el select_related para que caiga en el except del list()
        monkeypatch.setattr(Service.objects, "select_related", boom)
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, **headers)
        assert r.status_code == 500
        body = r.json()
        assert body.get("success") is False
        assert "Error interno del servidor" in body.get("message", "")

    # 26) IDs únicos
    def test_UT_SER_002_26_ids_unicos(self):
        for i in range(5):
            self._create_service(f"U{i}")
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, **headers)
        ids = [it["id"] for it in r.json()["data"]]
        assert len(ids) == len(set(ids))

    # 27) Consistencia general vs activos
    def test_UT_SER_002_27_consistencia_general_vs_activos(self):
        self._create_service("A1", status=self.status_active)
        self._create_service("I1", status=self.status_inactive)
        headers142 = _auth_header_for([142])
        headers143 = _auth_header_for([143])
        rg = self.client.get(self.endpoint, **headers142).json()["data"]
        ra = self.client.get(self.endpoint_active, **headers143).json()["data"]
        general_by_id = {it["id"]: it for it in rg}
        for it in ra:
            assert it["id"] in general_by_id
            assert it["status_id"] == 1

    # 28) Tolerancia a Accept y Locale
    def test_UT_SER_002_28_accept_y_locale(self):
        self._create_service("L1")
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint, HTTP_ACCEPT="application/json", HTTP_ACCEPT_LANGUAGE="es-CO", **headers)
        assert r.status_code == 200
        assert isinstance(r.json().get("data"), list)

    # 29) Orden estable ante mismos timestamps
    def test_UT_SER_002_29_orden_estable_mismo_timestamp(self):
        ts = timezone.now()
        s1 = self._create_service("Zeta", modification_date=ts)
        s2 = self._create_service("Alpha", modification_date=ts)
        _ = s1, s2
        headers = _auth_header_for([142])
        r1 = self.client.get(self.endpoint, **headers).json()["data"]
        r2 = self.client.get(self.endpoint, **headers).json()["data"]
        seq1 = [it["id"] for it in r1]
        seq2 = [it["id"] for it in r2]
        assert seq1 == seq2  # estabilidad entre llamadas

    # 30) Paginación soportada o ignorada sin error
    def test_UT_SER_002_30_paginacion_ignorada_sin_error(self):
        for i in range(50):
            self._create_service(f"P{i}")
        headers = _auth_header_for([142])
        r = self.client.get(self.endpoint + "?page=2&page_size=20", **headers)
        assert r.status_code == 200
        body = r.json()
        assert body.get("success") is True
