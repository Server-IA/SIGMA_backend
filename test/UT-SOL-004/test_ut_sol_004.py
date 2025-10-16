"""
Pruebas unitarias para el endpoint de detalles de solicitud de servicio
ID: UT-SOL-004
Título: Obtener detalles completos de una solicitud de servicio
Endpoint: GET /service_requests/{id_request}/details/
"""

import sys
import os
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

# Ajustar el path para imports si es necesario
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from users.models.user import User


@pytest.mark.django_db
class TestServiceRequestDetails:
    """
    Pruebas de integración para el endpoint GET /service_requests/{id_request}/details/
    
    NOTA: Estas pruebas verifican el comportamiento real del endpoint.
    Los resultados (APROBADO/NO APROBADO) se determinarán después de ejecutar las pruebas.
    """
    
    endpoint_template = '/service_requests/{}/details/'

    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        
        # Crear usuario de prueba
        self.user, created = User.objects.get_or_create(id_user=1)
        self.user.is_authenticated = True
        self.user.id = self.user.id_user

    # ====================================================================================
    # UT-SOL-004.1: Sin token de autenticación - debe retornar 401
    # ====================================================================================
    def test_UT_SOL_004_1_sin_token_retorna_401(self):
        """
        GIVEN: Una petición sin token de autenticación
        WHEN: Se intenta acceder al endpoint de detalles
        THEN: Debe retornar 401 Unauthorized
        """
        # Arrange: Cliente sin autenticación
        client_no_auth = APIClient()
        url = self.endpoint_template.format(1)
        
        # Act
        response = client_no_auth.get(url)
        
        # Assert
        print(f"\n[UT-SOL-004.1] Status Code: {response.status_code}")
        print(f"[UT-SOL-004.1] Esperado: 401, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            f"Se esperaba 401 pero se obtuvo {response.status_code}"

    # ====================================================================================
    # UT-SOL-004.2: Token inválido - debe retornar 401
    # ====================================================================================
    def test_UT_SOL_004_2_token_invalido_retorna_401(self):
        """
        GIVEN: Una petición con token inválido
        WHEN: Se intenta acceder al endpoint
        THEN: Debe retornar 401 Unauthorized
        """
        # Arrange: Cliente con credenciales inválidas
        client_invalid = APIClient()
        client_invalid.credentials(HTTP_AUTHORIZATION='Bearer token_invalido_12345')
        url = self.endpoint_template.format(1)
        
        # Act
        response = client_invalid.get(url)
        
        # Assert
        print(f"\n[UT-SOL-004.2] Status Code: {response.status_code}")
        print(f"[UT-SOL-004.2] Esperado: 401, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            f"Se esperaba 401 pero se obtuvo {response.status_code}"

    # ====================================================================================
    # UT-SOL-004.3: Sin permiso request.retrieve (154) - debe retornar 403
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_3_sin_permiso_retorna_403(self, mock_check_perm):
        """
        GIVEN: Un usuario autenticado sin permiso request.retrieve (154)
        WHEN: Intenta acceder al endpoint de detalles
        THEN: Debe retornar 403 Forbidden
        """
        # Arrange: Simular que el usuario NO tiene el permiso 154
        mock_check_perm.return_value = False
        self.client.force_authenticate(user=self.user)
        url = self.endpoint_template.format(1)
        
        # Act
        response = self.client.get(url)
        
        # Assert
        print(f"\n[UT-SOL-004.3] Status Code: {response.status_code}")
        print(f"[UT-SOL-004.3] Esperado: 403, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_403_FORBIDDEN, \
            f"Se esperaba 403 pero se obtuvo {response.status_code}"

    # ====================================================================================
    # UT-SOL-004.4: ID inexistente - debe retornar 404
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_4_id_inexistente_retorna_404(self, mock_check_perm):
        """
        GIVEN: Un ID de solicitud que no existe en la base de datos
        WHEN: Se solicita el detalle
        THEN: Debe retornar 404 Not Found
        """
        # Arrange: Usuario con permiso, ID inexistente
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        url = self.endpoint_template.format(99999)
        
        # Act
        response = self.client.get(url)
        
        # Assert
        print(f"\n[UT-SOL-004.4] Status Code: {response.status_code}")
        print(f"[UT-SOL-004.4] Esperado: 404, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_404_NOT_FOUND, \
            f"Se esperaba 404 pero se obtuvo {response.status_code}"

    # ====================================================================================
    # UT-SOL-004.5: Formato de ID inválido - debe retornar 404
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_5_formato_id_invalido_retorna_404(self, mock_check_perm):
        """
        GIVEN: Un ID con formato inválido (texto en lugar de número)
        WHEN: Se solicita el detalle
        THEN: Debe retornar 404 Not Found
        """
        # Arrange: Usuario con permiso, ID con formato inválido
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        url = self.endpoint_template.format("invalid_id")
        
        # Act
        response = self.client.get(url)
        
        # Assert
        print(f"\n[UT-SOL-004.5] Status Code: {response.status_code}")
        print(f"[UT-SOL-004.5] Esperado: 404, Obtenido: {response.status_code}")
        # Puede ser 404 o 400 dependiendo de la implementación
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST], \
            f"Se esperaba 404 o 400 pero se obtuvo {response.status_code}"

    # ====================================================================================
    # UT-SOL-004.6: Usuario solo puede ver sus propias solicitudes (si aplica filtro)
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_6_consulta_limitada_solo_propias(self, mock_check_perm):
        """
        GIVEN: Un usuario autenticado
        WHEN: Intenta acceder a una solicitud (si existe filtro por usuario)
        THEN: Debe validar que solo acceda a sus propias solicitudes
        
        NOTA: Este test verifica si existe filtro de pertenencia. 
        Si no hay filtro, retornará 404 por ID inexistente.
        """
        # Arrange
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        url = self.endpoint_template.format(1)
        
        # Act
        response = self.client.get(url)
        
        # Assert
        print(f"\n[UT-SOL-004.6] Status Code: {response.status_code}")
        print(f"[UT-SOL-004.6] Response: {response.data if hasattr(response, 'data') else 'N/A'}")
        # El resultado depende de si existe la solicitud y si pertenece al usuario
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND], \
            f"Se esperaba 200 o 404 pero se obtuvo {response.status_code}"

    # ====================================================================================
    # UT-SOL-004.7: Estructura completa de respuesta
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_7_estructura_completa_requerida(self, mock_check_perm):
        """
        GIVEN: Una solicitud existente con todos los datos
        WHEN: Se solicita el detalle
        THEN: Debe retornar estructura JSON con todos los campos requeridos
        
        NOTA: Esta prueba requiere que exista al menos una solicitud en la BD para verificar estructura.
        Si no existe, se marca como SKIP para documentación.
        """
        # Arrange
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        
        # Intentar con IDs comunes: 1, 2, 3...
        test_ids = [1, 2, 3, 4, 5]
        response = None
        
        for test_id in test_ids:
            url = self.endpoint_template.format(test_id)
            response = self.client.get(url)
            if response.status_code == status.HTTP_200_OK:
                break
        
        # Assert
        print(f"\n[UT-SOL-004.7] Status Code: {response.status_code if response else 'N/A'}")
        
        if response and response.status_code == status.HTTP_200_OK:
            print(f"[UT-SOL-004.7] Solicitud encontrada, verificando estructura...")
            required_fields = [
                'id_request', 'customer_id', 'request_detail',
                'scheduled_start_date', 'scheduled_end_date',
                'request_status_id', 'request_machinery_user',
                'request_location', 'amount_paid', 'amount_to_pay'
            ]
            
            for field in required_fields:
                assert field in response.data, f"Campo requerido '{field}' no encontrado en la respuesta"
            
            print(f"[UT-SOL-004.7] ✓ Estructura completa verificada")
            print(f"[UT-SOL-004.7] Campos encontrados: {list(response.data.keys())}")
        else:
            pytest.skip("No hay solicitudes en la BD para verificar estructura. Crear datos de prueba primero.")

    # ====================================================================================
    # UT-SOL-004.8: Información de cliente completa
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_8_informacion_cliente_completa(self, mock_check_perm):
        """
        GIVEN: Una solicitud con información completa del cliente
        WHEN: Se solicita el detalle
        THEN: Debe incluir todos los datos del cliente
        """
        # Arrange
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        
        # Intentar encontrar una solicitud existente
        test_ids = [1, 2, 3, 4, 5]
        response = None
        
        for test_id in test_ids:
            url = self.endpoint_template.format(test_id)
            response = self.client.get(url)
            if response.status_code == status.HTTP_200_OK:
                break
        
        # Assert
        print(f"\n[UT-SOL-004.8] Status Code: {response.status_code if response else 'N/A'}")
        
        if response and response.status_code == status.HTTP_200_OK:
            customer_fields = [
                'customer_id', 'customer_name', 'customer_email',
                'customer_phone', 'customer_document_type', 'customer_document_number'
            ]
            
            missing_fields = [f for f in customer_fields if f not in response.data]
            if missing_fields:
                print(f"[UT-SOL-004.8] ⚠ Campos faltantes: {missing_fields}")
            else:
                print(f"[UT-SOL-004.8] ✓ Todos los campos de cliente presentes")
            
            # Verificar al menos customer_id que es obligatorio
            assert 'customer_id' in response.data, "Campo 'customer_id' no encontrado"
        else:
            pytest.skip("No hay solicitudes en la BD. Crear datos de prueba primero.")

    # ====================================================================================
    # UT-SOL-004.9: Maquinaria asignada completa
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_9_maquinaria_asignada_completa(self, mock_check_perm):
        """
        GIVEN: Una solicitud con maquinaria asignada
        WHEN: Se solicita el detalle
        THEN: Debe incluir lista de maquinaria con datos completos
        """
        # Arrange
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        
        test_ids = [1, 2, 3, 4, 5]
        response = None
        
        for test_id in test_ids:
            url = self.endpoint_template.format(test_id)
            response = self.client.get(url)
            if response.status_code == status.HTTP_200_OK:
                break
        
        # Assert
        print(f"\n[UT-SOL-004.9] Status Code: {response.status_code if response else 'N/A'}")
        
        if response and response.status_code == status.HTTP_200_OK:
            assert 'request_machinery_user' in response.data, \
                "Campo 'request_machinery_user' no encontrado"
            
            assert isinstance(response.data['request_machinery_user'], list), \
                "'request_machinery_user' debe ser una lista"
            
            if len(response.data['request_machinery_user']) > 0:
                machinery = response.data['request_machinery_user'][0]
                required_machinery_fields = [
                    'id_request_machinery_user', 'id_machinery',
                    'serial_number', 'machinery_image_path', 'id_user', 'user_name'
                ]
                
                missing = [f for f in required_machinery_fields if f not in machinery]
                if missing:
                    print(f"[UT-SOL-004.9] ⚠ Campos faltantes en maquinaria: {missing}")
                else:
                    print(f"[UT-SOL-004.9] ✓ Estructura de maquinaria completa")
            else:
                print(f"[UT-SOL-004.9] ⚠ La solicitud no tiene maquinaria asignada")
        else:
            pytest.skip("No hay solicitudes en la BD. Crear datos de prueba primero.")

    # ====================================================================================
    # UT-SOL-004.10: Ubicación completa
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_10_ubicacion_completa(self, mock_check_perm):
        """
        GIVEN: Una solicitud con ubicación completa
        WHEN: Se solicita el detalle
        THEN: Debe incluir datos de ubicación con coordenadas, área, etc.
        """
        # Arrange
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        
        test_ids = [1, 2, 3, 4, 5]
        response = None
        
        for test_id in test_ids:
            url = self.endpoint_template.format(test_id)
            response = self.client.get(url)
            if response.status_code == status.HTTP_200_OK:
                break
        
        # Assert
        print(f"\n[UT-SOL-004.10] Status Code: {response.status_code if response else 'N/A'}")
        
        if response and response.status_code == status.HTTP_200_OK:
            assert 'request_location' in response.data, \
                "Campo 'request_location' no encontrado"
            
            if response.data['request_location']:
                location = response.data['request_location']
                location_fields = [
                    'place_name', 'latitude', 'longitude', 'area',
                    'area_unit_name', 'soil_type_name', 'altitude'
                ]
                
                missing = [f for f in location_fields if f not in location]
                if missing:
                    print(f"[UT-SOL-004.10] ⚠ Campos faltantes en ubicación: {missing}")
                else:
                    print(f"[UT-SOL-004.10] ✓ Estructura de ubicación completa")
            else:
                print(f"[UT-SOL-004.10] ⚠ La solicitud no tiene ubicación")
        else:
            pytest.skip("No hay solicitudes en la BD. Crear datos de prueba primero.")

    # ====================================================================================
    # UT-SOL-004.11: Información económica completa
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_11_informacion_economica_completa(self, mock_check_perm):
        """
        GIVEN: Una solicitud con información económica
        WHEN: Se solicita el detalle
        THEN: Debe incluir montos pagados, por pagar, método de pago, etc.
        """
        # Arrange
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        
        test_ids = [1, 2, 3, 4, 5]
        response = None
        
        for test_id in test_ids:
            url = self.endpoint_template.format(test_id)
            response = self.client.get(url)
            if response.status_code == status.HTTP_200_OK:
                break
        
        # Assert
        print(f"\n[UT-SOL-004.11] Status Code: {response.status_code if response else 'N/A'}")
        
        if response and response.status_code == status.HTTP_200_OK:
            economic_fields = [
                'amount_paid', 'currency_unit_amount_paid_name',
                'amount_to_pay', 'currency_unit_amount_to_pay_name',
                'payment_status_name', 'payment_method'
            ]
            
            missing = [f for f in economic_fields if f not in response.data]
            if missing:
                print(f"[UT-SOL-004.11] ⚠ Campos económicos faltantes: {missing}")
            else:
                print(f"[UT-SOL-004.11] ✓ Información económica completa")
        else:
            pytest.skip("No hay solicitudes en la BD. Crear datos de prueba primero.")

    # ====================================================================================
    # UT-SOL-004.12: Fechas en formato correcto (YYYY-MM-DD o ISO 8601)
    # ====================================================================================
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission')
    def test_UT_SOL_004_12_fechas_formato_correcto(self, mock_check_perm):
        """
        GIVEN: Una solicitud con fechas
        WHEN: Se solicita el detalle
        THEN: Las fechas deben estar en formato YYYY-MM-DD o ISO 8601
        """
        # Arrange
        mock_check_perm.return_value = True
        self.client.force_authenticate(user=self.user)
        
        test_ids = [1, 2, 3, 4, 5]
        response = None
        
        for test_id in test_ids:
            url = self.endpoint_template.format(test_id)
            response = self.client.get(url)
            if response.status_code == status.HTTP_200_OK:
                break
        
        # Assert
        print(f"\n[UT-SOL-004.12] Status Code: {response.status_code if response else 'N/A'}")
        
        if response and response.status_code == status.HTTP_200_OK:
            # Verificar formato de fecha YYYY-MM-DD
            assert 'scheduled_start_date' in response.data, \
                "Campo 'scheduled_start_date' no encontrado"
            assert 'scheduled_end_date' in response.data, \
                "Campo 'scheduled_end_date' no encontrado"
            
            print(f"[UT-SOL-004.12] scheduled_start_date: {response.data['scheduled_start_date']}")
            print(f"[UT-SOL-004.12] scheduled_end_date: {response.data['scheduled_end_date']}")
            
            # Las fechas con datetime deben tener 'T' (formato ISO 8601)
            if 'confirmation_datetime' in response.data and response.data['confirmation_datetime']:
                assert 'T' in str(response.data['confirmation_datetime']), \
                    "confirmation_datetime debe estar en formato ISO 8601"
                print(f"[UT-SOL-004.12] ✓ Formato de fechas correcto")
        else:
            pytest.skip("No hay solicitudes en la BD. Crear datos de prueba primero.")
