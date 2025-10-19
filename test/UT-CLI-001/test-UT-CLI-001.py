"""
Pruebas unitarias para el endpoint de creación de clientes
ID: UT-CLI-001 (RF-057-01)
Título: Registrar cliente
"""

import sys
import os
import pytest
from datetime import datetime
from unittest.mock import patch, Mock
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

# Ajustar el path para imports si es necesario
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from service_requests.models.customer import Customer
from service_requests.models.document_type import DocumentType
from service_requests.models.person_type import PersonType
from users.models.user import User
from parameterization.models import Statues, StatuesCategory

import inspect

@pytest.mark.django_db
class TestCustomerCreation:
    endpoint = '/customers/create_customer/'

    def setup_method(self):
        self.client = APIClient()
        
        # Crear usuario responsable y autenticado
        self.user, created = User.objects.get_or_create(id_user=1)
        self.user.is_authenticated = True
        self.user.id = self.user.id_user
        
        # Mock JWT authentication
        self.mock_jwt_payload = {
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "rol": [{
                "id": 1,
                "name": "Admin",
                "permisos": [{"id": 133, "name": "customer.create"}]
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
        
        # Crear estado activo
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
        
        # Crear tipos de documento
        self.document_type, created = DocumentType.objects.get_or_create(
            id_document_type=3,
            defaults={'name': 'Cédula ciudadanía'}
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
        
        # Crear usuario de prueba en el servicio users (simulado)
        self.test_user, created = User.objects.get_or_create(
            id_user=1,
            defaults={}
        )
        
        # Limpiar clientes existentes con documentos de prueba
        Customer.objects.filter(document_number__in=['1179172209', '1234567890']).delete()

    def mock_auth_service_response(self, document_number, user_exists=True):
        """Mock para simular respuestas del servicio de usuarios"""
        if document_number == '1179172209' and user_exists:
            return {
                'success': True,
                'data': {
                    'id': 1,
                    'name': 'Juan camilo',
                    'last_name': 'Sarmiento Cardozo',
                    'document_number': 1179172209,
                    'type_document': 3,
                    'email': 'juanandresveru@gmail.com',
                    'phone': '3001234567'
                }
            }
        else:
            return {'success': False, 'message': 'Usuario no encontrado'}

    @patch('service_requests.serializers.customer_serializers.customer_create_serializer.requests.get')
    def test_UT_CLI_001_caso_1_con_id_user(self, mock_requests_get):
        """UT-CLI-001 Caso 1: Creación con id_user existente"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": 1,
            "person_type": 1,
            "document_number": "1179172209",
            "type_document_id": 3,
            "check_digit": 12313,
            "legal_entity_name": "voldemort",
            "name": "Juan",
            "first_last_name": "Pérez",
            "second_last_name": "Gómez",
            "email": "juan.perez@example.com",
            "phone": "3001234567",
            "address": "Calle 123...",
            "id_municipality": 1,
            "tax_regime": 2
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Verificar respuesta exitosa
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['message'] == 'Cliente creado exitosamente'
        assert 'id_customer' in response_data
        
        # Verificar en base de datos que solo se guardó id_user y person_type
        customer = Customer.objects.get(id_customer=response_data['id_customer'])
        assert customer.id_user.id_user == 1
        assert customer.person_type.id_person_type == 1
        # Verificar que otros campos fueron ignorados o son null
        assert customer.document_number is None or customer.document_number != 1179172209
        assert customer.name is None or customer.name != "Juan"

    @patch('service_requests.serializers.customer_serializers.customer_create_serializer.requests.get')
    def test_UT_CLI_001_caso_2_document_number_existente(self, mock_requests_get):
        """UT-CLI-001 Caso 2: Document_number existente en users"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        # Mock respuesta del servicio de usuarios
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_auth_service_response('1179172209', True)
        mock_requests_get.return_value = mock_response
        
        data = {
            "id_user": None,
            "person_type": 1,
            "document_number": "1179172209",
            "type_document_id": 3,
            "check_digit": 12313,
            "legal_entity_name": "voldemort",
            "name": "Juan",
            "first_last_name": "Pérez",
            "second_last_name": "Gómez",
            "email": "juan.perez@example.com",
            "phone": "3001234567",
            "address": "Calle 123...",
            "id_municipality": 1,
            "tax_regime": 2
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Verificar respuesta exitosa
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['message'] == 'Cliente creado exitosamente'
        assert 'id_customer' in response_data
        
        # Verificar en base de datos que se encontró automáticamente el usuario
        customer = Customer.objects.get(id_customer=response_data['id_customer'])
        assert customer.id_user.id_user == 1
        assert customer.person_type.id_person_type == 1

    @patch('service_requests.serializers.customer_serializers.customer_create_serializer.requests.get')
    def test_UT_CLI_001_caso_3_cliente_nuevo(self, mock_requests_get):
        """UT-CLI-001 Caso 3: Cliente completamente nuevo"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        # Mock respuesta del servicio de usuarios (usuario no encontrado)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'success': False, 'message': 'Usuario no encontrado'}
        mock_requests_get.return_value = mock_response
        
        data = {
            "id_user": None,
            "person_type": 2,
            "document_number": "1234567890",
            "type_document_id": 3,
            "check_digit": 5,
            "legal_entity_name": "Empresa Test",
            "name": "Pedro",
            "first_last_name": "González",
            "second_last_name": "López",
            "email": "pedro.gonzalez@test.com",
            "phone": "3009876543",
            "address": "Carrera 45 #12-34",
            "id_municipality": 2,
            "tax_regime": 1
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Verificar respuesta exitosa
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['message'] == 'Cliente creado exitosamente'
        assert 'id_customer' in response_data
        
        # Verificar en base de datos que se guardaron todos los datos
        customer = Customer.objects.get(id_customer=response_data['id_customer'])
        assert customer.document_number == 1234567890
        assert customer.person_type.id_person_type == 2
        assert customer.name == "Pedro"
        assert customer.first_last_name == "González"
        assert customer.second_last_name == "López"
        assert customer.email == "pedro.gonzalez@test.com"
        assert customer.phone == "3009876543"
        assert customer.address == "Carrera 45 #12-34"
        assert customer.id_municipality == 2
        assert customer.tax_regime == 1
        assert customer.id_user is None

    def test_UT_CLI_001_document_number_negativo(self):
        """UT-CLI-001: Validación de document_number negativo"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": None,
            "person_type": 1,
            "document_number": -1234567890,
            "type_document_id": 3,
            "check_digit": 5,
            "legal_entity_name": "Empresa Test",
            "name": "Pedro",
            "first_last_name": "González",
            "second_last_name": "López",
            "email": "pedro.gonzalez@test.com",
            "phone": "3009876543",
            "address": "Carrera 45 #12-34",
            "id_municipality": 2,
            "tax_regime": 1
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 400
        response_data = response.json()
        assert response_data['success'] is False
        assert response_data['message'] == 'Error de validación'
        assert 'document_number' in response_data['errors']
        assert "El número de documento no puede ser negativo" in response_data['errors']['document_number'][0]

    def test_UT_CLI_001_document_number_mas_10_digitos(self):
        """UT-CLI-001: Validación de document_number con más de 10 dígitos"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": None,
            "person_type": 1,
            "document_number": 12345678901,  # 11 dígitos
            "type_document_id": 3,
            "check_digit": 5,
            "legal_entity_name": "Empresa Test",
            "name": "Pedro",
            "first_last_name": "González",
            "second_last_name": "López",
            "email": "pedro.gonzalez@test.com",
            "phone": "3009876543",
            "address": "Carrera 45 #12-34",
            "id_municipality": 2,
            "tax_regime": 1
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 400
        response_data = response.json()
        assert response_data['success'] is False
        assert response_data['message'] == 'Error de validación'
        assert 'document_number' in response_data['errors']
        assert "El número de documento no puede tener más de 10 dígitos" in response_data['errors']['document_number'][0]

    def test_UT_CLI_001_document_number_duplicado(self):
        """UT-CLI-001: Validación de document_number duplicado"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Crear cliente existente
        Customer.objects.create(
            document_number=1234567890,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Existente",
            id_municipality=1,
            tax_regime=1,
            customer_statues=self.active_status,
            id_responsible_user=self.user
        )
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": None,
            "person_type": 1,
            "document_number": 1234567890,  # Mismo documento
            "type_document_id": 3,
            "check_digit": 5,
            "legal_entity_name": "Empresa Test",
            "name": "Pedro",
            "first_last_name": "González",
            "second_last_name": "López",
            "email": "pedro.gonzalez@test.com",
            "phone": "3009876543",
            "address": "Carrera 45 #12-34",
            "id_municipality": 2,
            "tax_regime": 1
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 400
        response_data = response.json()
        assert response_data['success'] is False
        assert response_data['message'] == 'Error de validación'
        assert 'document_number' in response_data['errors']
        assert "Ya existe un cliente con este número de documento" in response_data['errors']['document_number'][0]

    def test_UT_CLI_001_campos_longitud_maxima(self):
        """UT-CLI-001: Validación de campos con longitud mayor a max_length"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": None,
            "person_type": 1,
            "document_number": 1234567890,
            "type_document_id": 3,
            "check_digit": 5,
            "legal_entity_name": "A" * 101,  # Más de 100 caracteres
            "name": "B" * 101,  # Más de 100 caracteres
            "first_last_name": "C" * 101,  # Más de 100 caracteres
            "second_last_name": "D" * 101,  # Más de 100 caracteres
            "email": "E" * 101,  # Más de 100 caracteres
            "phone": "F" * 101,  # Más de 100 caracteres
            "address": "G" * 101,  # Más de 100 caracteres
            "id_municipality": 2,
            "tax_regime": 1
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 400
        response_data = response.json()
        assert response_data['success'] is False
        assert response_data['message'] == 'Error de validación'
        # Verificar que al menos algunos campos con longitud excesiva están en los errores
        errors = response_data['errors']
        long_fields = ['legal_entity_name', 'name', 'first_last_name', 'second_last_name', 'email', 'phone', 'address']
        assert any(field in errors for field in long_fields)

    def test_UT_CLI_001_person_type_obligatorio(self):
        """UT-CLI-001: Validación de person_type obligatorio ausente"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": None,
            # "person_type": 1,  # Campo obligatorio ausente
            "document_number": 1234567890,
            "type_document_id": 3,
            "check_digit": 5,
            "legal_entity_name": "Empresa Test",
            "name": "Pedro",
            "first_last_name": "González",
            "second_last_name": "López",
            "email": "pedro.gonzalez@test.com",
            "phone": "3009876543",
            "address": "Carrera 45 #12-34",
            "id_municipality": 2,
            "tax_regime": 1
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 400
        response_data = response.json()
        assert response_data['success'] is False
        assert response_data['message'] == 'Error de validación'
        assert 'person_type' in response_data['errors']

    def test_UT_CLI_001_sin_token(self):
        """UT-CLI-001: Prueba sin token de autenticación"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Remover autenticación
        self.client.force_authenticate(user=None)
        
        data = {
            "id_user": None,
            "person_type": 1,
            "document_number": 1234567890,
            "type_document_id": 3,
            "check_digit": 5,
            "legal_entity_name": "Empresa Test",
            "name": "Pedro",
            "first_last_name": "González",
            "second_last_name": "López",
            "email": "pedro.gonzalez@test.com",
            "phone": "3009876543",
            "address": "Carrera 45 #12-34",
            "id_municipality": 2,
            "tax_regime": 1
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 401
        response_data = response.json()
        assert 'detail' in response_data
        assert "Authentication credentials were not provided" in response_data['detail']

    def test_UT_CLI_001_sin_permisos(self):
        """UT-CLI-001: Prueba con usuario sin permisos customer.create"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Crear usuario sin permisos
        user_without_permission, created = User.objects.get_or_create(id_user=2)
        user_without_permission.is_authenticated = True
        user_without_permission.id = user_without_permission.id_user
        
        # Mock JWT payload sin permisos
        mock_jwt_payload_no_perms = {
            "id": 2,
            "email": "test2@example.com",
            "name": "Test User 2",
            "rol": [{
                "id": 2,
                "name": "User",
                "permisos": [{"id": 999, "name": "other.permission"}]  # Permiso diferente
            }]
        }
        
        # Mock authentication
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 2
        mock_user.auth = mock_jwt_payload_no_perms
        self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": None,
            "person_type": 1,
            "document_number": 1234567890,
            "type_document_id": 3,
            "check_digit": 5,
            "legal_entity_name": "Empresa Test",
            "name": "Pedro",
            "first_last_name": "González",
            "second_last_name": "López",
            "email": "pedro.gonzalez@test.com",
            "phone": "3009876543",
            "address": "Carrera 45 #12-34",
            "id_municipality": 2,
            "tax_regime": 1
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 403
        response_data = response.json()
        assert response_data['message'] == "No tiene permisos para crear clientes"

    def test_UT_CLI_001_tiempo_respuesta(self):
        """UT-CLI-001: Validación de tiempo de respuesta menor a 3 segundos"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": 1,
            "person_type": 1,
            "document_number": "1179172209",
            "type_document_id": 3,
            "check_digit": 12313,
            "legal_entity_name": "voldemort",
            "name": "Juan",
            "first_last_name": "Pérez",
            "second_last_name": "Gómez",
            "email": "juan.perez@example.com",
            "phone": "3001234567",
            "address": "Calle 123...",
            "id_municipality": 1,
            "tax_regime": 2
        }
        
        import time
        start_time = time.time()
        response = self.client.post(self.endpoint, data, format='json')
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"Response Time: {response_time:.3f} seconds")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Verificar tiempo de respuesta
        assert response_time < 3.0, f"Tiempo de respuesta {response_time:.3f}s excede los 3 segundos"
        
        # Verificar respuesta exitosa
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['success'] is True

    def test_UT_CLI_001_estructura_json_respuesta(self):
        """UT-CLI-001: Validación de estructura JSON de respuesta consistente"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        
        # Mock para simular que el usuario tiene permisos
        with patch.object(self.client, 'force_authenticate') as mock_auth:
            mock_auth.return_value = None
            
            # Mock JWT payload con permisos
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            mock_user.auth = self.mock_jwt_payload
            self.client.force_authenticate(user=mock_user)
        
        data = {
            "id_user": 1,
            "person_type": 1,
            "document_number": "1179172209",
            "type_document_id": 3,
            "check_digit": 12313,
            "legal_entity_name": "voldemort",
            "name": "Juan",
            "first_last_name": "Pérez",
            "second_last_name": "Gómez",
            "email": "juan.perez@example.com",
            "phone": "3001234567",
            "address": "Calle 123...",
            "id_municipality": 1,
            "tax_regime": 2
        }
        
        response = self.client.post(self.endpoint, data, format='json')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Verificar estructura JSON consistente
        assert response.status_code == 201
        response_data = response.json()
        
        # Verificar campos obligatorios en respuesta exitosa
        required_fields = ['success', 'message', 'id_customer']
        for field in required_fields:
            assert field in response_data, f"Campo '{field}' faltante en respuesta exitosa"
        
        # Verificar tipos de datos
        assert isinstance(response_data['success'], bool)
        assert isinstance(response_data['message'], str)
        assert isinstance(response_data['id_customer'], int)
        
        # Verificar valores específicos
        assert response_data['success'] is True
        assert response_data['message'] == 'Cliente creado exitosamente'
        assert response_data['id_customer'] > 0
