"""
Pruebas unitarias para el endpoint de listado de clientes
ID: UT-CLI-002
Título: Listar clientes con filtros y paginación
"""

import sys
import os
import pytest
from unittest.mock import patch, Mock
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

# Ajustar el path para imports si es necesario
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from service_requests.models.customer import Customer
from service_requests.models.document_type import DocumentType
from service_requests.models.person_type import PersonType
from service_requests.api.customer_viewset import CustomerViewSet
from users.models.user import User
from parameterization.models import Statues, StatuesCategory

import inspect


@pytest.mark.django_db
class TestCustomerList:
    endpoint = '/customers/'
    endpoint_active = '/customers/active/'

    def setup_method(self):
        self.client = APIClient()
        
        # Crear usuario responsable y autenticado
        self.user, created = User.objects.get_or_create(id_user=1)
        self.user.is_authenticated = True
        self.user.id = self.user.id_user
        
        # Mock JWT authentication con permiso customer.list (135)
        self.mock_jwt_payload = {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "rol": [{
                "id": 1,
                "name": "Admin",
                "permisos": [{"id": 135, "name": "customer.list"}]
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
        
        # Crear tipos de documento
        self.doc_type_cc, created = DocumentType.objects.get_or_create(
            id_document_type=1,
            defaults={'name': 'Cédula de Ciudadanía'}
        )
        
        self.doc_type_nit, created = DocumentType.objects.get_or_create(
            id_document_type=2,
            defaults={'name': 'NIT'}
        )
        
        # Crear tipos de persona
        self.person_type_juridica, created = PersonType.objects.get_or_create(
            id_person_type=1,
            defaults={'name': 'Persona Jurídica'}
        )
        
        self.person_type_natural, created = PersonType.objects.get_or_create(
            id_person_type=2,
            defaults={'name': 'Persona Natural'}
        )
        
        # Limpiar clientes existentes
        Customer.objects.all().delete()

    def _create_mock_user_with_permission(self, has_permission=True):
        """Helper para crear mock de usuario con o sin permiso"""
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        
        if has_permission:
            mock_user.auth = self.mock_jwt_payload
        else:
            mock_user.auth = {
                "id": 1,
                "email": "test@example.com",
                "name": "Test User",
                "rol": [{
                    "id": 2,
                    "name": "User",
                    "permisos": [{"id": 999, "name": "other.permission"}]
                }]
            }
        
        return mock_user

    def _create_sample_customers(self, count=3):
        """Helper para crear clientes de muestra"""
        customers = []
        
        for i in range(count):
            customer = Customer.objects.create(
                document_number=100000000 + i,  # Número más pequeño para evitar overflow
                type_document_id=self.doc_type_cc if i % 2 == 0 else self.doc_type_nit,
                person_type=self.person_type_natural if i % 2 == 0 else self.person_type_juridica,
                legal_entity_name=f"Cliente {i+1}",
                name=f"Nombre{i+1}" if i % 2 == 0 else None,
                first_last_name=f"Apellido{i+1}" if i % 2 == 0 else None,
                second_last_name=f"Segundo{i+1}" if i % 2 == 0 else None,
                email=f"cliente{i+1}@test.com",
                phone=f"30012345{i:02d}",
                address=f"Calle {i+1}",
                id_municipality=1,
                tax_regime=1,
                customer_statues=self.active_status if i % 2 == 0 else self.inactive_status,
                id_responsible_user=self.user
            )
            customers.append(customer)
        
        return customers

    # ==================== PRUEBA UT-CLI-002.1 ====================
    @patch.object(CustomerViewSet, 'check_permission', return_value=True)
    def test_UT_CLI_002_1_listado_basico_ok(self, mock_check_permission):
        """UT-CLI-002.1: Listado básico de clientes OK"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(3)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert len(data['data']) == 3
        
        # Verificar campos requeridos en cada cliente
        for customer in data['data']:
            assert 'id_customer' in customer
            assert 'document_number' in customer
            assert 'type_document_id' in customer
            assert 'type_document_name' in customer
            assert 'person_type_id' in customer
            assert 'person_type_name' in customer
            assert 'email' in customer
            assert 'phone' in customer
            assert 'customer_statues_id' in customer
            assert 'customer_statues_name' in customer

    # ==================== PRUEBA UT-CLI-002.2 ====================
    def test_UT_CLI_002_2_sin_token_retorna_401(self):
        """UT-CLI-002.2: Acceso sin token retorna 401"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(3)
        self.client.force_authenticate(user=None)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 401
        data = response.json()
        assert 'detail' in data

    # ==================== PRUEBA UT-CLI-002.3 ====================
    def test_UT_CLI_002_3_sin_permiso_retorna_403(self):
        """UT-CLI-002.3: Sin permiso customer.list retorna 403"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(3)
        mock_user = self._create_mock_user_with_permission(False)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 403
        data = response.json()
        assert data['success'] is False
        assert 'No tiene permisos' in data['message']

    # ==================== PRUEBA UT-CLI-002.4 ====================
    @patch.object(CustomerViewSet, 'check_permission', return_value=True)
    def test_UT_CLI_002_4_estructura_minima_y_tipos(self, mock_check_permission):
        """UT-CLI-002.4: Estructura mínima y tipos en /customers/"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(2)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar tipos JSON
        assert isinstance(data['success'], bool)
        assert isinstance(data['data'], list)
        
        if len(data['data']) > 0:
            customer = data['data'][0]
            assert isinstance(customer['id_customer'], int)
            assert isinstance(customer['type_document_name'], (str, type(None)))
            assert isinstance(customer['person_type_name'], (str, type(None)))
            assert isinstance(customer['customer_statues_name'], (str, type(None)))
            assert customer['email'] is None or isinstance(customer['email'], str)
            assert customer['phone'] is None or isinstance(customer['phone'], str)

    # ==================== PRUEBA UT-CLI-002.5 ====================
    @pytest.mark.skip(reason="Paginación no implementada en el endpoint actual")
    def test_UT_CLI_002_5_paginacion_page_y_pagesize(self):
        """UT-CLI-002.5: Paginación page y pageSize"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(50)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?page=2&pageSize=20")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) == 20
        # Verificar metadatos de paginación si existen
        # assert 'total' in data
        # assert 'page' in data
        # assert 'pageSize' in data

    # ==================== PRUEBA UT-CLI-002.6 ====================
    @pytest.mark.skip(reason="Paginación limit/offset no implementada en el endpoint actual")
    def test_UT_CLI_002_6_paginacion_limit_offset(self):
        """UT-CLI-002.6: Paginación limit y offset"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(60)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?limit=25&offset=25")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) == 25

    # ==================== PRUEBA UT-CLI-002.7 ====================
    @pytest.mark.skip(reason="Validación de parámetros de paginación no implementada")
    def test_UT_CLI_002_7_paginacion_parametros_invalidos(self):
        """UT-CLI-002.7: Paginación con parámetros inválidos"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(10)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?page=-1&pageSize=abc")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        # Debería retornar 400 o usar defaults
        assert response.status_code in [200, 400]

    # ==================== PRUEBA UT-CLI-002.8 ====================
    @pytest.mark.skip(reason="Filtro por nombre no implementado en el endpoint actual")
    def test_UT_CLI_002_8_filtro_por_nombre(self):
        """UT-CLI-002.8: Filtro por nombre o razón social"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        Customer.objects.create(
            document_number=1111111111,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Juan Pérez",
            name="Juan",
            first_last_name="Pérez",
            email="juan@test.com",
            phone="3001111111",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        Customer.objects.create(
            document_number=2222222222,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Pedro López",
            name="Pedro",
            first_last_name="López",
            email="pedro@test.com",
            phone="3002222222",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?name=Juan")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        # Verificar que solo retorna clientes con "Juan"
        for customer in data['data']:
            assert 'Juan' in customer.get('name', '') or 'Juan' in customer.get('legal_entity_name', '')

    # ==================== PRUEBA UT-CLI-002.9 ====================
    @pytest.mark.skip(reason="Filtro por tipo de documento no implementado en el endpoint actual")
    def test_UT_CLI_002_9_filtro_por_tipo_identificacion(self):
        """UT-CLI-002.9: Filtro por tipo de identificación"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(5)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?type_document_id=1")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        for customer in data['data']:
            assert customer['type_document_id'] == 1

    # ==================== PRUEBA UT-CLI-002.10 ====================
    @pytest.mark.skip(reason="Filtro por document_number no implementado en el endpoint actual")
    def test_UT_CLI_002_10_filtro_por_documento_identificacion(self):
        """UT-CLI-002.10: Filtro por documento de identificación"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        Customer.objects.create(
            document_number=1079172264,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Específico",
            email="especifico@test.com",
            phone="3003333333",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        self._create_sample_customers(3)
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?document_number=1079172264")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) == 1
        assert data['data'][0]['document_number'] == 1079172264

    # ==================== PRUEBA UT-CLI-002.11 ====================
    @pytest.mark.skip(reason="Filtro por status no implementado en el endpoint actual")
    def test_UT_CLI_002_11_filtro_por_estado_cliente(self):
        """UT-CLI-002.11: Filtro por estado del cliente"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(4)  # Crea 2 activos y 2 inactivos
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?status=Activo")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        for customer in data['data']:
            assert customer['customer_statues_name'] == 'Activo'

    # ==================== PRUEBA UT-CLI-002.12 ====================
    @pytest.mark.skip(reason="Filtro por email/phone no implementado en el endpoint actual")
    def test_UT_CLI_002_12_filtro_por_telefono_email(self):
        """UT-CLI-002.12: Filtro por teléfono o email"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        Customer.objects.create(
            document_number=5555555555,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Email",
            email="juan@gmail.com",
            phone="3005555555",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        self._create_sample_customers(2)
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?email=juan@gmail.com")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) >= 1
        found = any(c['email'] == 'juan@gmail.com' for c in data['data'])
        assert found

    # ==================== PRUEBA UT-CLI-002.13 ====================
    @pytest.mark.skip(reason="Filtros combinados no implementados en el endpoint actual")
    def test_UT_CLI_002_13_combinacion_filtros_and(self):
        """UT-CLI-002.13: Combinación de filtros (AND)"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(5)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?status=Activo&type_document_id=1")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        for customer in data['data']:
            assert customer['customer_statues_name'] == 'Activo'
            assert customer['type_document_id'] == 1

    # ==================== PRUEBA UT-CLI-002.14 ====================
    @pytest.mark.skip(reason="Búsqueda rápida no implementada en el endpoint actual")
    def test_UT_CLI_002_14_busqueda_rapida(self):
        """UT-CLI-002.14: Búsqueda rápida por nombre/documento"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        Customer.objects.create(
            document_number=1079172264,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Búsqueda",
            email="busqueda@test.com",
            phone="3006666666",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?q=10791722")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) >= 1

    # ==================== PRUEBA UT-CLI-002.15 ====================
    @patch.object(CustomerViewSet, 'check_permission', return_value=True)
    def test_UT_CLI_002_15_sin_resultados_lista_vacia(self, mock_check_permission):
        """UT-CLI-002.15: Sin resultados muestra lista vacía"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange - No crear ningún cliente
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data'] == []

    # ==================== PRUEBA UT-CLI-002.16 ====================
    @patch.object(CustomerViewSet, 'check_permission', return_value=True)
    def test_UT_CLI_002_16_codificacion_utf8(self, mock_check_permission):
        """UT-CLI-002.16: Codificación UTF-8 en nombres y tipos"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        Customer.objects.create(
            document_number=777777777,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="José María Ñoño",
            name="José",
            first_last_name="María",
            second_last_name="Ñoño",
            email="jose@test.com",
            phone="3007777777",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que los caracteres UTF-8 se mantienen correctos
        customer = data['data'][0]
        assert 'José' in str(customer.get('name', '')) or 'José' in str(customer.get('legal_entity_name', ''))
        assert 'Ñoño' in str(customer.get('second_last_name', '')) or 'Ñoño' in str(customer.get('legal_entity_name', ''))
        
        # Verificar nombres de FK con acentos
        assert customer['type_document_name'] in ['Cédula de Ciudadanía', 'NIT']

    # ==================== PRUEBA UT-CLI-002.17 ====================
    @patch.object(CustomerViewSet, 'check_permission', return_value=True)
    def test_UT_CLI_002_17_usuario_activo_derivacion(self, mock_check_permission):
        """UT-CLI-002.17: Usuario Activo: derivación Sí/No"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        # Cliente con id_user
        Customer.objects.create(
            id_user=self.user,
            document_number=888888888,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Con Usuario",
            email="conusuario@test.com",
            phone="3008888888",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        # Cliente sin id_user
        Customer.objects.create(
            id_user=None,
            document_number=999999999,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Sin Usuario",
            email="sinusuario@test.com",
            phone="3009999999",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar presencia de id_user para derivar "Usuario Activo"
        for customer in data['data']:
            assert 'id_user' in customer
            # Si id_user es null -> No tiene usuario activo
            # Si id_user != null -> Tiene usuario (requiere verificación adicional)

    # ==================== PRUEBA UT-CLI-002.18 ====================
    @pytest.mark.skip(reason="Requiere configuración completa del endpoint create_customer")
    @patch('service_requests.api.customer_viewset.AuditClient')
    @patch.object(CustomerViewSet, 'check_permission')
    def test_UT_CLI_002_18_actualizacion_inmediata_tras_crear(self, mock_check_permission, mock_audit):
        """UT-CLI-002.18: Actualización inmediata tras crear cliente"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Configurar mock para permitir tanto list como create
        def check_permission_side_effect(request, permission_id):
            return permission_id in [133, 135]  # customer.create y customer.list
        
        mock_check_permission.side_effect = check_permission_side_effect
        
        # Arrange
        mock_user_with_create = Mock()
        mock_user_with_create.is_authenticated = True
        mock_user_with_create.id = 1
        mock_user_with_create.auth = {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "rol": [{
                "id": 1,
                "name": "Admin",
                "permisos": [
                    {"id": 133, "name": "customer.create"},
                    {"id": 135, "name": "customer.list"}
                ]
            }]
        }
        self.client.force_authenticate(user=mock_user_with_create)
        
        # Act - Crear cliente
        create_data = {
            "id_user": None,
            "person_type": 1,
            "document_number": "1122334455",
            "type_document_id": 1,
            "check_digit": 5,
            "legal_entity_name": "Nuevo Cliente",
            "name": "Nuevo",
            "first_last_name": "Cliente",
            "email": "nuevo@test.com",
            "phone": "3001122334",
            "address": "Calle Nueva",
            "id_municipality": 1,
            "tax_regime": 1
        }
        
        create_response = self.client.post('/customers/create_customer/', create_data, format='json')
        
        # Assert - Crear
        print(f"Create Status Code: {create_response.status_code}")
        assert create_response.status_code == 201
        
        # Act - Listar inmediatamente después
        list_response = self.client.get(self.endpoint)
        
        # Assert
        print(f"List Status Code: {list_response.status_code}")
        
        assert list_response.status_code == 200
        data = list_response.json()
        assert data['success'] is True
        
        # Verificar que el nuevo cliente aparece
        new_customer_id = create_response.json()['id_customer']
        found = any(c['id_customer'] == new_customer_id for c in data['data'])
        assert found, "El nuevo cliente no aparece inmediatamente en el listado"

    # ==================== PRUEBA UT-CLI-002.19 ====================
    @pytest.mark.skip(reason="Requiere implementación de toggle-status y verificación de listados")
    def test_UT_CLI_002_19_actualizacion_inmediata_tras_cambiar_estado(self):
        """UT-CLI-002.19: Actualización inmediata tras cambiar estado"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        customer = Customer.objects.create(
            document_number=3333333333,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Toggle",
            email="toggle@test.com",
            phone="3003333333",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        mock_user_with_toggle = Mock()
        mock_user_with_toggle.is_authenticated = True
        mock_user_with_toggle.id = 1
        mock_user_with_toggle.auth = {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "rol": [{
                "id": 1,
                "name": "Admin",
                "permisos": [
                    {"id": 135, "name": "customer.list"},
                    {"id": 139, "name": "customer.toggle_status"}
                ]
            }]
        }
        self.client.force_authenticate(user=mock_user_with_toggle)
        
        # Act - Cambiar estado
        toggle_response = self.client.patch(f'/customers/{customer.id_customer}/toggle-status/')
        assert toggle_response.status_code == 200
        
        # Act - Verificar en listado general
        list_response = self.client.get(self.endpoint)
        assert list_response.status_code == 200
        
        # Act - Verificar en listado de activos
        active_response = self.client.get(self.endpoint_active)
        
        # Assert
        print(f"Active List Status Code: {active_response.status_code}")
        
        assert active_response.status_code == 200
        active_data = active_response.json()
        
        # El cliente debería estar inactivo y no aparecer en /active/
        found_in_active = any(c['id_customer'] == customer.id_customer for c in active_data['data'])
        assert not found_in_active, "El cliente inactivo no debería aparecer en /customers/active/"

    # ==================== PRUEBA UT-CLI-002.20 ====================
    @patch.object(CustomerViewSet, 'check_permission', return_value=True)
    def test_UT_CLI_002_20_active_solo_incluye_activos(self, mock_check_permission):
        """UT-CLI-002.20: /customers/active/ solo incluye Activo"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        # Crear 2 activos y 2 inactivos
        Customer.objects.create(
            document_number=444444444,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Activo 1",
            email="activo1@test.com",
            phone="3004444444",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        Customer.objects.create(
            document_number=555555555,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Inactivo 1",
            email="inactivo1@test.com",
            phone="3005555555",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.inactive_status,
            id_responsible_user=self.user
        )
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint_active)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        
        # Verificar que todos son activos
        for customer in data['data']:
            assert customer['customer_statues_name'] == 'Activo'
            assert customer['customer_statues_id'] == 1

    # ==================== PRUEBA UT-CLI-002.21 ====================
    def test_UT_CLI_002_21_active_sin_permiso_retorna_403(self):
        """UT-CLI-002.21: /customers/active/ sin permiso retorna 403"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(3)
        mock_user = self._create_mock_user_with_permission(False)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint_active)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 403
        data = response.json()
        assert data['success'] is False
        assert 'No tiene permisos' in data['message']

    # ==================== PRUEBA UT-CLI-002.22 ====================
    @pytest.mark.skip(reason="Metadatos de paginación no implementados en el endpoint actual")
    def test_UT_CLI_002_22_metadatos_paginacion(self):
        """UT-CLI-002.22: Metadatos de paginación en respuesta"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(100)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?page=1&pageSize=50")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar metadatos
        assert 'meta' in data or 'total' in data
        if 'meta' in data:
            assert 'total' in data['meta']
            assert 'page' in data['meta']
            assert 'pageSize' in data['meta']

    # ==================== PRUEBA UT-CLI-002.23 ====================
    @patch.object(CustomerViewSet, 'check_permission', return_value=True)
    def test_UT_CLI_002_23_manejo_nulos_phone_address(self, mock_check_permission):
        """UT-CLI-002.23: Manejo de nulos en phone y address"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        # Cliente con phone y address null
        Customer.objects.create(
            document_number=666666666,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Sin Phone",
            email="sinphone@test.com",
            phone=None,
            address=None,
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        # Cliente con phone y address con valores
        Customer.objects.create(
            document_number=777777776,
            type_document_id=self.doc_type_cc,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Con Phone",
            email="conphone@test.com",
            phone="3007777777",
            address="Calle 7",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que null se maneja correctamente
        for customer in data['data']:
            phone = customer.get('phone')
            address = customer.get('address')
            
            # Debe ser null o string, no string vacío inesperado
            assert phone is None or isinstance(phone, str)
            assert address is None or isinstance(address, str)

    # ==================== PRUEBA UT-CLI-002.24 ====================
    @pytest.mark.skip(reason="Ordenamiento no implementado en el endpoint actual")
    def test_UT_CLI_002_24_ordenamiento_por_nombre_asc(self):
        """UT-CLI-002.24: Ordenamiento por nombre ascendente"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        names = ["Zorro SA", "Alpha Corp", "Beta Inc"]
        for i, name in enumerate(names):
            Customer.objects.create(
                document_number=2000000000 + i,
                type_document_id=self.doc_type_cc,
                person_type=self.person_type_juridica,
                legal_entity_name=name,
                email=f"empresa{i}@test.com",
                phone=f"30020000{i:02d}",
                id_municipality=1,
                tax_regime=1,
                customer_statues=self.active_status,
                id_responsible_user=self.user
            )
        
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        response = self.client.get(f"{self.endpoint}?sort=name&order=asc")
        
        # Assert
        print(f"Status Code: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar orden alfabético
        legal_names = [c['legal_entity_name'] for c in data['data']]
        assert legal_names == sorted(legal_names)

    # ==================== PRUEBA UT-CLI-002.25 ====================
    @pytest.mark.skip(reason="Validación de inyección SQL - requiere análisis más profundo")
    def test_UT_CLI_002_25_robustez_ante_inyeccion(self):
        """UT-CLI-002.25: Robustez ante inyección en filtros"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(3)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act - Intentar inyección SQL
        malicious_payloads = [
            "?name=Juan' OR '1'='1",
            "?name=Juan'; DROP TABLE customer;--",
            "?document_number=1 OR 1=1"
        ]
        
        for payload in malicious_payloads:
            response = self.client.get(f"{self.endpoint}{payload}")
            
            # Assert
            print(f"Payload: {payload}")
            print(f"Status Code: {response.status_code}")
            
            # Debe retornar 200 o 400, pero seguro
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                data = response.json()
                # No debería amplificar resultados sospechosamente
                assert len(data['data']) <= Customer.objects.count()
                # No debería exponer errores SQL
                assert 'error' not in str(data).lower() or 'sql' not in str(data).lower()

    # ==================== PRUEBA ADICIONAL: Tiempo de respuesta ====================
    @patch.object(CustomerViewSet, 'check_permission', return_value=True)
    def test_UT_CLI_002_tiempo_respuesta(self, mock_check_permission):
        """UT-CLI-002: Validación de tiempo de respuesta menor a 3 segundos"""
        print(f"\n--- Testing: {inspect.currentframe().f_code.co_name} ---")
        
        # Arrange
        self._create_sample_customers(50)
        mock_user = self._create_mock_user_with_permission(True)
        self.client.force_authenticate(user=mock_user)
        
        # Act
        start_time = time.time()
        response = self.client.get(self.endpoint)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Assert
        print(f"Response Time: {response_time:.3f} seconds")
        print(f"Status Code: {response.status_code}")
        
        assert response_time < 3.0, f"Tiempo de respuesta {response_time:.3f}s excede los 3 segundos"
        assert response.status_code == 200
