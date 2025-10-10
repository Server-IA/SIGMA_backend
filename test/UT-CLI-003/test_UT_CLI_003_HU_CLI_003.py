"""
Pruebas unitarias para el endpoint de detalle de cliente
ID: UT-CLI-003 a UT-CLI-003.7 (HU-CLI-003)
"""

import sys
import os
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import json

# Ajustar el path para imports antes de configurar Django
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from service_requests.models.customer import Customer
from service_requests.models.document_type import DocumentType
from service_requests.models.person_type import PersonType
from users.models.user import User
from parameterization.models import Statues, StatuesCategory

import inspect


@pytest.mark.django_db
class TestCustomerDetail:
    base_endpoint = '/customers'

    def setup_method(self):
        self.client = APIClient()
        
        # Crear usuario responsable y autenticado
        self.user, created = User.objects.get_or_create(id_user=1)
        self.user.is_authenticated = True
        self.user.id = self.user.id_user
        self.client.force_authenticate(user=self.user)
        
        now = timezone.now()
        
        # Categoría de estados
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
        
        # Estados necesarios
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
        
        # Tipo de documento
        self.document_type, created = DocumentType.objects.get_or_create(
            id_document_type=1,
            defaults={
                'name': 'Cédula de Ciudadanía'
            }
        )
        
        # Tipo de persona
        self.person_type, created = PersonType.objects.get_or_create(
            id_person_type=1,
            defaults={
                'name': 'Persona Natural'
            }
        )
        
        # Crear clientes para las pruebas
        self.create_test_customers()

    def create_test_customers(self):
        """Crear clientes para las pruebas"""
        # Limpiar clientes existentes
        Customer.objects.filter(id_customer__in=[49, 50]).delete()
        
        now = timezone.now()
        
        # Cliente con id_user (ID=49) - para el camino feliz
        self.customer_with_user = Customer.objects.create(
            id_customer=49,
            id_user=self.user,
            document_number=12345678,
            type_document_id=self.document_type,
            check_digit=9,
            person_type=self.person_type,
            legal_entity_name='Empresa Test',
            name='Juan',
            first_last_name='Pérez',
            second_last_name='García',
            email='juan.perez@test.com',
            phone='3001234567',
            address='Calle 123 #45-67',
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        # Cliente sin id_user (ID=50)
        self.customer_without_user = Customer.objects.create(
            id_customer=50,
            id_user=None,
            document_number=87654321,
            type_document_id=self.document_type,
            check_digit=1,
            person_type=self.person_type,
            legal_entity_name='Empresa Test 2',
            name='María',
            first_last_name='López',
            second_last_name='Martínez',
            email='maria.lopez@test.com',
            phone='3007654321',
            address='Carrera 78 #90-12',
            id_municipality=2,
            tax_regime=2,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )

    @patch('service_requests.api.customer_viewset.CustomerViewSet.check_permission')
    def test_UT_CLI_003_detalle_exitoso_con_id_user(self, mock_check_permission):
        """UT-CLI-003: 200 OK – Detalle obtenido exitosamente (camino feliz, cliente con id_user)"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        endpoint = f'{self.base_endpoint}/49/detail/'
        print(f"Endpoint: {endpoint} (Method: GET)")
        print(f"Description: {self.__doc__}")
        
        mock_check_permission.return_value = True
        
        response = self.client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['message'] == "Detalle del cliente obtenido exitosamente"
        assert 'data' in response_data
        
        # Verificar campos principales en data
        data = response_data['data']
        assert data['id_customer'] == 49
        assert data['id_user'] == self.user.id_user
        assert data['document_number'] == 12345678
        assert data['name'] == 'Juan'
        assert data['first_last_name'] == 'Pérez'
        assert data['email'] == 'juan.perez@test.com'
        assert data['phone'] == '3001234567'
        assert data['address'] == 'Calle 123 #45-67'

    @patch('service_requests.api.customer_viewset.CustomerViewSet.check_permission')
    def test_UT_CLI_003_1_detalle_exitoso_sin_id_user(self, mock_check_permission):
        """UT-CLI-003.1: 200 OK – Detalle obtenido exitosamente (cliente sin id_user)"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        endpoint = f'{self.base_endpoint}/50/detail/'
        print(f"Endpoint: {endpoint} (Method: GET)")
        print(f"Description: {self.__doc__}")
        
        mock_check_permission.return_value = True
        
        response = self.client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['message'] == "Detalle del cliente obtenido exitosamente"
        assert 'data' in response_data
        
        # Verificar que id_user es null
        data = response_data['data']
        assert data['id_customer'] == 50
        assert data['id_user'] is None
        assert data['document_number'] == 87654321
        assert data['name'] == 'María'
        assert data['first_last_name'] == 'López'

    @patch('service_requests.api.customer_viewset.CustomerViewSet.check_permission')
    def test_UT_CLI_003_2_cliente_inexistente(self, mock_check_permission):
        """UT-CLI-003.2: 404 Not Found – Cliente inexistente"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        endpoint = f'{self.base_endpoint}/9999/detail/'
        print(f"Endpoint: {endpoint} (Method: GET)")
        print(f"Description: {self.__doc__}")
        
        mock_check_permission.return_value = True
        
        response = self.client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 404
        response_data = response.json()
        assert response_data['success'] is False
        assert response_data['message'] == "Cliente no encontrado"

    def test_UT_CLI_003_3_usuario_sin_permiso(self):
        """UT-CLI-003.3: 403 Forbidden – Usuario sin permiso 134"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        endpoint = f'{self.base_endpoint}/49/detail/'
        print(f"Endpoint: {endpoint} (Method: GET)")
        print(f"Description: {self.__doc__}")
        
        # Crear usuario sin permisos
        user_without_permission, created = User.objects.get_or_create(id_user=99)
        user_without_permission.is_authenticated = True
        user_without_permission.id = user_without_permission.id_user
        self.client.force_authenticate(user=user_without_permission)
        
        response = self.client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 403
        response_data = response.json()
        assert response_data['success'] is False
        assert response_data['message'] == "No tiene permisos para ver el detalle del cliente."

    @patch('service_requests.api.customer_viewset.CustomerViewSet.check_permission')
    @patch('service_requests.models.customer.Customer.objects.select_related')
    def test_UT_CLI_003_4_error_interno_servidor(self, mock_select_related, mock_check_permission):
        """UT-CLI-003.4: 500 Internal Server Error – Excepción no controlada"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        endpoint = f'{self.base_endpoint}/49/detail/'
        print(f"Endpoint: {endpoint} (Method: GET)")
        print(f"Description: {self.__doc__}")
        
        mock_check_permission.return_value = True
        
        # Simular excepción en la consulta
        mock_query = MagicMock()
        mock_query.get.side_effect = Exception("Error de base de datos")
        mock_select_related.return_value = mock_query
        
        response = self.client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 500
        response_data = response.json()
        assert response_data['success'] is False
        assert response_data['message'] == "Error al procesar la solicitud"

    @patch('service_requests.api.customer_viewset.CustomerViewSet.check_permission')
    def test_UT_CLI_003_5_validacion_campos_obligatorios(self, mock_check_permission):
        """UT-CLI-003.5: Validación de campos obligatorios en data serializada"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        endpoint = f'{self.base_endpoint}/49/detail/'
        print(f"Endpoint: {endpoint} (Method: GET)")
        print(f"Description: {self.__doc__}")
        
        mock_check_permission.return_value = True
        
        response = self.client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data['data']
        
        # Verificar campos obligatorios presentes
        required_fields = [
            'type_document_id', 'document_number', 'check_digit', 
            'person_type_name', 'name', 'first_last_name', 
            'email', 'phone', 'address', 'customer_statues_name'
        ]
        
        for field in required_fields:
            assert field in data, f"Campo '{field}' no encontrado en la respuesta"
            assert data[field] is not None, f"Campo '{field}' es nulo"

    @patch('service_requests.api.customer_viewset.CustomerViewSet.check_permission')
    def test_UT_CLI_003_6_validacion_tipos_datos(self, mock_check_permission):
        """UT-CLI-003.6: Validación del serializer – Tipos de datos correctos"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        endpoint = f'{self.base_endpoint}/49/detail/'
        print(f"Endpoint: {endpoint} (Method: GET)")
        print(f"Description: {self.__doc__}")
        
        mock_check_permission.return_value = True
        
        response = self.client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        data = response_data['data']
        
        # Verificar tipos de datos
        assert isinstance(data['id_customer'], int), "id_customer debe ser int"
        assert isinstance(data['id_user'], int), "id_user debe ser int"
        assert isinstance(data['document_number'], int), "document_number debe ser int"
        assert isinstance(data['check_digit'], int), "check_digit debe ser int"
        assert isinstance(data['name'], str), "name debe ser str"
        assert isinstance(data['first_last_name'], str), "first_last_name debe ser str"
        assert isinstance(data['email'], str), "email debe ser str"
        assert isinstance(data['phone'], str), "phone debe ser str"
        assert isinstance(data['address'], str), "address debe ser str"
        assert isinstance(data['person_type_name'], str), "person_type_name debe ser str"
        assert isinstance(data['customer_statues_name'], str), "customer_statues_name debe ser str"

    @patch('service_requests.api.customer_viewset.CustomerViewSet.check_permission')
    def test_UT_CLI_003_7_estructura_respuesta_exitosa(self, mock_check_permission):
        """UT-CLI-003.7: Validar mensaje y estructura de respuesta exitosa"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        endpoint = f'{self.base_endpoint}/49/detail/'
        print(f"Endpoint: {endpoint} (Method: GET)")
        print(f"Description: {self.__doc__}")
        
        mock_check_permission.return_value = True
        
        response = self.client.get(endpoint)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Verificar estructura estándar de respuesta
        assert 'success' in response_data, "Campo 'success' no encontrado"
        assert 'message' in response_data, "Campo 'message' no encontrado"
        assert 'data' in response_data, "Campo 'data' no encontrado"
        
        # Verificar valores específicos
        assert response_data['success'] is True
        assert response_data['message'] == "Detalle del cliente obtenido exitosamente"
        assert isinstance(response_data['data'], dict), "data debe ser un diccionario"
        
        # Verificar que data contiene información del cliente
        data = response_data['data']
        assert 'id_customer' in data
        assert 'name' in data
        assert 'email' in data
