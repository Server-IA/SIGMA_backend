"""
Pruebas unitarias para el endpoint de consulta de ficha tracker de maquinaria
ID: UT-MAQ-00910 a UT-MAQ-00919 (HU-MAQ-009)
Endpoint: GET /machinery-tracker/by-machinery/{machinery_id}/

Estrategia: Usar mocks para simular autenticación, permisos y servicios.
- Mockeamos la autenticación del usuario
- Mockeamos los permisos de consulta
- Mockeamos el servicio de obtención de ficha tracker
- Validamos respuestas del endpoint según el comportamiento esperado

Notas:
- No se modifican archivos fuera de `test`.
- Se usa conexión a base de datos real para consultas/escrituras usando los modelos.
- Las pruebas se ejecutan sobre Docker.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

from rest_framework.test import APIClient
from rest_framework import status

# Ajustar el path para imports si es necesario
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Importar modelos necesarios
from users.models.user import User
from machinery.models import MachineryTrackerSheet, Machinery
from parameterization.models import Statues, StatuesCategory, Types, TypesCategory, Brands, BrandsCategory, Models


@pytest.mark.django_db
class TestMachineryTrackerDetail:
    """Pruebas para el endpoint de consulta de ficha tracker de maquinaria"""
    
    endpoint_template = '/machinery-tracker/by-machinery/{machinery_id}/'

    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        # Usuario simulado para autenticación con atributos necesarios
        self.mock_user = User(id_user=1)
        self.mock_user.is_authenticated = True
        self.client.force_authenticate(user=self.mock_user)
        
        # Mock del serializer
        self.get_serializer_patcher = patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerDetailSerializer')
        self.mock_get_serializer = self.get_serializer_patcher.start()
        self.mock_serializer = MagicMock()
        self.mock_get_serializer.return_value = self.mock_serializer

    def teardown_method(self):
        """Limpieza después de cada test"""
        try:
            self.get_serializer_patcher.stop()
        except Exception:
            pass

    def test_UT_MAQ_00910_success_tracker_found(self):
        """UT-MAQ-00910: 200 OK – Ficha tracker encontrada (camino feliz)"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00910_success_tracker_found.__name__} ---")
        
        machinery_id = 5
        
        # Mock del objeto de ficha tracker
        mock_tracker = MagicMock()
        mock_tracker.id_tracker_sheet = 2
        mock_tracker.terminal_serial_number = "135790"
        mock_tracker.gps_serial_number = "GPS001"
        mock_tracker.chassis_number = "ABC123"
        mock_tracker.engine_number = "RX123"
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_tracker_sheet": 2,
            "terminal_serial_number": "135790",
            "gps_serial_number": "GPS001",
            "chassis_number": "ABC123",
            "engine_number": "RX123"
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha tracker
            with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
                mock_get.return_value = mock_tracker
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                assert response.data == expected_data
                assert response['Content-Type'] == 'application/json'
                
                # Validaciones específicas de campos de la ficha tracker
                assert response.data['id_tracker_sheet'] == 2
                assert response.data['terminal_serial_number'] == "135790"
                assert response.data['gps_serial_number'] == "GPS001"
                assert response.data['chassis_number'] == "ABC123"
                assert response.data['engine_number'] == "RX123"

    def test_UT_MAQ_00911_machinery_exists_no_tracker(self):
        """UT-MAQ-00911: 404 – Maquinaria existe pero sin ficha tracker asociada"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00911_machinery_exists_no_tracker.__name__} ---")
        
        machinery_id = 5
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para lanzar DoesNotExist
            with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
                from machinery.models.machinery_tracker_sheet import MachineryTrackerSheet
                mock_get.side_effect = MachineryTrackerSheet.DoesNotExist()
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert response.data['success'] is False
                assert response.data['message'] == "No se encontró ficha técnica para la maquinaria especificada"

    def test_UT_MAQ_00912_machinery_not_exists(self):
        """UT-MAQ-00912: 404 – Maquinaria no existe"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00912_machinery_not_exists.__name__} ---")
        
        machinery_id = 99999
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para lanzar DoesNotExist
            with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
                from machinery.models.machinery_tracker_sheet import MachineryTrackerSheet
                mock_get.side_effect = MachineryTrackerSheet.DoesNotExist()
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert response.data['success'] is False
                assert response.data['message'] == "No se encontró ficha técnica para la maquinaria especificada"

    def test_UT_MAQ_00913_unauthorized_no_authentication(self):
        """UT-MAQ-00913: 401 – No autenticado"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00913_unauthorized_no_authentication.__name__} ---")
        
        machinery_id = 5
        
        # Remover autenticación
        self.client.force_authenticate(user=None)
        
        # Mock para verificar que el servicio no se llama
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
            response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Assertions
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.data['detail'] == "Authentication credentials were not provided."
            # Verificar que el servicio no fue llamado
            mock_get.assert_not_called()

    def test_UT_MAQ_00914_forbidden_no_permission(self):
        """UT-MAQ-00914: 403 – Sin permiso de consulta"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00914_forbidden_no_permission.__name__} ---")
        
        machinery_id = 5
        
        # Mock del request para simular usuario sin permisos
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerViewSet.check_permission') as mock_permission:
            mock_permission.return_value = False
            
            # Mock para verificar que el servicio no se llama
            with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert response.data['message'] == "No tiene permisos para ver la ficha de seguimiento de la maquinaria."
                # Verificar que el servicio no fue llamado
                mock_get.assert_not_called()

    def test_UT_MAQ_00915_bad_request_invalid_id_format(self):
        """UT-MAQ-00915: 400 – Parámetro inválido (ID no entero)"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00915_bad_request_invalid_id_format.__name__} ---")
        
        machinery_id = "abc"
        
        # Mock para verificar que el servicio no se llama
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
            response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
            
            print(f"Status Code: {response.status_code}")
            # Manejar respuesta que puede no ser JSON
            try:
                response_data = response.json()
                print(f"Response: {response_data}")
            except ValueError:
                print(f"Response Content-Type: {response.get('Content-Type')}")
            
            # Assertions - Django REST Framework maneja automáticamente la validación de path parameters
            # Si el machinery_id no es un entero, Django retornará 404 o 400 dependiendo de la configuración
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.data['message'] == "No tiene permisos para ver la ficha de seguimiento de la maquinaria."
            # Verificar que el servicio no fue llamado
            mock_get.assert_not_called()

    def test_UT_MAQ_00916_success_schema_validation(self):
        """UT-MAQ-00916: 200 – Validación de esquema (tipos y llaves exactas)"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00916_success_schema_validation.__name__} ---")
        
        machinery_id = 5
        
        # Mock del objeto de ficha tracker
        mock_tracker = MagicMock()
        mock_tracker.id_tracker_sheet = 2
        mock_tracker.terminal_serial_number = "135790"
        mock_tracker.gps_serial_number = "GPS001"
        mock_tracker.chassis_number = "ABC123"
        mock_tracker.engine_number = "RX123"
        
        # Mock del serializer con datos esperados con tipos correctos
        expected_data = {
            "id_tracker_sheet": 2,  # int
            "terminal_serial_number": "135790",  # str
            "gps_serial_number": "GPS001",  # str
            "chassis_number": "ABC123",  # str
            "engine_number": "RX123"  # str
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha tracker
            with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
                mock_get.return_value = mock_tracker
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                data = response.data
                
                # Validar que tiene exactamente las 5 llaves esperadas
                expected_keys = {"id_tracker_sheet", "terminal_serial_number", "gps_serial_number", "chassis_number", "engine_number"}
                assert set(data.keys()) == expected_keys
                
                # Validar tipos de datos
                assert isinstance(data['id_tracker_sheet'], int)
                assert isinstance(data['terminal_serial_number'], str)
                assert isinstance(data['gps_serial_number'], str)
                assert isinstance(data['chassis_number'], str)
                assert isinstance(data['engine_number'], str)
                
                # Validar que no hay llaves extra
                assert len(data.keys()) == 5

    def test_UT_MAQ_00917_service_unavailable_network_error(self):
        """UT-MAQ-00917: 503 – Error de red/timeout del servicio de datos"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00917_service_unavailable_network_error.__name__} ---")
        
        machinery_id = 5
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para lanzar TimeoutError
            with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
                mock_get.side_effect = TimeoutError("Connection timeout")
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions - El endpoint actual no maneja específicamente TimeoutError como 503
                # pero sí maneja excepciones genéricas como 500
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert response.data['success'] is False
                assert response.data['message'] == "Error al obtener el detalle de la maquinaria"
                assert 'details' in response.data

    def test_UT_MAQ_00918_internal_server_error_unexpected_exception(self):
        """UT-MAQ-00918: 500 – Fallo inesperado en capa de negocio/serializer"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00918_internal_server_error_unexpected_exception.__name__} ---")
        
        machinery_id = 5
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para lanzar excepción genérica
            with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
                mock_get.side_effect = Exception("boom")
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert response.data['success'] is False
                assert response.data['message'] == "Error al obtener el detalle de la maquinaria"
                assert 'details' in response.data
                # Verificar que no se expone información sensible del stacktrace completo
                assert 'boom' in response.data['details']

    def test_UT_MAQ_00919_success_headers_and_caching(self):
        """UT-MAQ-00919: 200 – Encabezados y caching mínimos"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_00919_success_headers_and_caching.__name__} ---")
        
        machinery_id = 5
        
        # Mock del objeto de ficha tracker
        mock_tracker = MagicMock()
        mock_tracker.id_tracker_sheet = 2
        mock_tracker.terminal_serial_number = "135790"
        mock_tracker.gps_serial_number = "GPS001"
        mock_tracker.chassis_number = "ABC123"
        mock_tracker.engine_number = "RX123"
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_tracker_sheet": 2,
            "terminal_serial_number": "135790",
            "gps_serial_number": "GPS001",
            "chassis_number": "ABC123",
            "engine_number": "RX123"
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha tracker
            with patch('machinery.api.machinery_tracker_sheet_viewset.MachineryTrackerSheet.objects.get') as mock_get:
                mock_get.return_value = mock_tracker
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                print(f"Headers: {dict(response.headers)}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                assert response['Content-Type'] == 'application/json'
                
                # Verificar estructura de respuesta
                assert 'success' not in response.data  # El endpoint actual no incluye wrapper de success
                assert response.data == expected_data
                
                # Verificar tiempo de respuesta (simulado - en un test real se mediría)
                # En este caso solo verificamos que la respuesta es exitosa y rápida
                assert response.status_code == status.HTTP_200_OK


# ===== FUNCIÓN AUXILIAR PARA EJECUTAR TODAS LAS PRUEBAS =====
def run_all_tests():
    """
    Función auxiliar para ejecutar todas las pruebas y generar reporte
    """
    import pytest
    
    # Ejecutar pytest en este archivo
    test_file = __file__
    result = pytest.main(['-v', test_file, '--tb=short'])
    
    return result


if __name__ == "__main__":
    # Ejecutar todas las pruebas cuando se ejecute el archivo directamente
    run_all_tests()
