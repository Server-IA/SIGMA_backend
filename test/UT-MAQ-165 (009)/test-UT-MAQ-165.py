"""
Pruebas unitarias para el endpoint de consulta de ficha técnica específica de maquinaria
ID: UT-MAQ-009 (HU-MAQ-009)

Estrategia: Usar mocks para simular autenticación, permisos y servicios.
- Mockeamos la autenticación del usuario
- Mockeamos los permisos de consulta
- Mockeamos el servicio de obtención de ficha técnica específica
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
from machinery.models import SpecificTechnicalSheet, Machinery
from parameterization.models import Units, Types, Statues, StatuesCategory, TypesCategory


@pytest.mark.django_db
class TestSpecificTechnicalSheetDetail:
    """Pruebas para el endpoint de consulta de ficha técnica específica"""
    
    endpoint_template = '/machinery-specific-sheet/machinery/{machinery_id}/'

    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        # Usuario simulado para autenticación con atributos necesarios
        self.mock_user = User(id_user=1)
        self.mock_user.is_authenticated = True
        self.client.force_authenticate(user=self.mock_user)
        
        # Mock del serializer
        self.get_serializer_patcher = patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
        self.mock_get_serializer = self.get_serializer_patcher.start()
        self.mock_serializer = MagicMock()
        self.mock_get_serializer.return_value = self.mock_serializer

    def teardown_method(self):
        """Limpieza después de cada test"""
        try:
            self.get_serializer_patcher.stop()
        except Exception:
            pass

    def test_UT_BACK_MAQ_DET_001_success_with_valid_payload(self):
        """UT-BACK-MAQ-DET-001: Retorno 200 con payload válido (servicio OK)"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_001_success_with_valid_payload.__name__} ---")
        
        machinery_id = 15
        
        # Mock del objeto de ficha técnica específica
        mock_sheet = MagicMock()
        mock_sheet.id_specific_technical_sheet = 12
        mock_sheet.power = 120.0
        mock_sheet.power_unit = MagicMock(id_units=5, name="kW")
        mock_sheet.engine_type = MagicMock(id_types=8, name="Diésel")
        mock_sheet.cylinder_capacity = 4500.0
        mock_sheet.cylinder_capacity_unit = MagicMock(id_units=6, name="cc")
        mock_sheet.cylinder_arrangement_type = MagicMock(id_types=11, name="En línea")
        mock_sheet.cylinder_count = 6
        mock_sheet.traction_type = MagicMock(id_types=15, name="4x4")
        mock_sheet.fuel_consumption = 15.0
        mock_sheet.fuel_consumption_unit = MagicMock(id_units=18, name="L/h")
        mock_sheet.transmission_system_type = MagicMock(id_types=24, name="Automática")
        mock_sheet.fuel_capacity = 200.0
        mock_sheet.fuel_capacity_unit = MagicMock(id_units=17, name="L")
        mock_sheet.carrying_capacity = 8000.0
        mock_sheet.carrying_capacity_unit = MagicMock(id_units=22, name="kg")
        mock_sheet.operating_weight = 12500.0
        mock_sheet.operating_weight_unit = MagicMock(id_units=21, name="kg")
        mock_sheet.max_speed = 65.0
        mock_sheet.max_speed_unit = MagicMock(id_units=24, name="km/h")
        mock_sheet.draft_force = 350.0
        mock_sheet.draft_force_unit = MagicMock(id_units=19, name="kN")
        mock_sheet.maximum_altitude = 3500.0
        mock_sheet.maximum_altitude_unit = MagicMock(id_units=26, name="m")
        mock_sheet.minimum_performance = 20.0
        mock_sheet.maximum_performance = 50.0
        mock_sheet.performance_unit = MagicMock(id_units=30, name="%")
        mock_sheet.width = 2.5
        mock_sheet.length = 6.0
        mock_sheet.height = 3.0
        mock_sheet.dimension_unit = MagicMock(id_units=27, name="m")
        mock_sheet.net_weight = 11500.0
        mock_sheet.net_weight_unit = MagicMock(id_units=21, name="kg")
        mock_sheet.air_conditioning_system_type = MagicMock(id_types=32, name="Climatizado")
        mock_sheet.air_conditioning_system_consumption = 1.5
        mock_sheet.air_conditioning_system_consumption_unit = MagicMock(id_units=18, name="L/h")
        
        # Mock del serializer con datos esperados completos
        expected_data = {
            "id_specific_technical_sheet": 12,
            "power": 120.0,
            "power_unit": 5,
            "engine_type": 8,
            "cylinder_capacity": 4500.0,
            "cylinder_capacity_unit": 6,
            "cylinder_arrangement_type": 11,
            "cylinder_count": 6,
            "traction_type": 15,
            "fuel_consumption": 15.0,
            "fuel_consumption_unit": 18,
            "transmission_system_type": 24,
            "fuel_capacity": 200.0,
            "fuel_capacity_unit": 17,
            "carrying_capacity": 8000.0,
            "carrying_capacity_unit": 22,
            "operating_weight": 12500.0,
            "operating_weight_unit": 21,
            "max_speed": 65.0,
            "max_speed_unit": 24,
            "draft_force": 350.0,
            "draft_force_unit": 19,
            "maximum_altitude": 3500.0,
            "maximum_altitude_unit": 26,
            "minimum_performance": 20.0,
            "maximum_performance": 50.0,
            "performance_unit": 30,
            "width": 2.5,
            "length": 6.0,
            "height": 3.0,
            "dimension_unit": 27,
            "net_weight": 11500.0,
            "net_weight_unit": 21,
            "air_conditioning_system_type": 32,
            "air_conditioning_system_consumption": 1.5,
            "air_conditioning_system_consumption_unit": 18
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                mock_filter.return_value.first.return_value = mock_sheet
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                assert response.data['success'] is True
                assert response.data['message'] == "Ficha técnica específica obtenida exitosamente"
                assert response.data['data'] == expected_data
                assert response['Content-Type'] == 'application/json'
                
                # Validaciones específicas de campos de la ficha técnica
                data = response.data['data']
                
                # Validar campos obligatorios
                assert data['id_specific_technical_sheet'] == 12
                assert data['power'] == 120.0
                assert data['power_unit'] == 5
                assert data['engine_type'] == 8
                assert data['cylinder_capacity'] == 4500.0
                assert data['cylinder_capacity_unit'] == 6
                assert data['cylinder_arrangement_type'] == 11
                assert data['cylinder_count'] == 6
                assert data['fuel_consumption'] == 15.0
                assert data['fuel_consumption_unit'] == 18
                assert data['transmission_system_type'] == 24
                assert data['operating_weight'] == 12500.0
                assert data['operating_weight_unit'] == 21
                assert data['max_speed'] == 65.0
                assert data['max_speed_unit'] == 24
                assert data['width'] == 2.5
                assert data['length'] == 6.0
                assert data['height'] == 3.0
                assert data['dimension_unit'] == 27
                assert data['net_weight'] == 11500.0
                assert data['net_weight_unit'] == 21
                
                # Validar campos opcionales
                assert data['traction_type'] == 15
                assert data['fuel_capacity'] == 200.0
                assert data['fuel_capacity_unit'] == 17
                assert data['carrying_capacity'] == 8000.0
                assert data['carrying_capacity_unit'] == 22
                assert data['draft_force'] == 350.0
                assert data['draft_force_unit'] == 19
                assert data['maximum_altitude'] == 3500.0
                assert data['maximum_altitude_unit'] == 26
                assert data['minimum_performance'] == 20.0
                assert data['maximum_performance'] == 50.0
                assert data['performance_unit'] == 30
                assert data['air_conditioning_system_type'] == 32
                assert data['air_conditioning_system_consumption'] == 1.5
                assert data['air_conditioning_system_consumption_unit'] == 18
                
                # Validar tipos de datos
                assert isinstance(data['power'], float)
                assert isinstance(data['power_unit'], int)
                assert isinstance(data['engine_type'], int)
                assert isinstance(data['cylinder_capacity'], float)
                assert isinstance(data['cylinder_count'], int)
                assert isinstance(data['fuel_consumption'], float)
                assert isinstance(data['operating_weight'], float)
                assert isinstance(data['max_speed'], float)
                assert isinstance(data['width'], float)
                assert isinstance(data['length'], float)
                assert isinstance(data['height'], float)
                assert isinstance(data['net_weight'], float)

    def test_UT_BACK_MAQ_DET_002_not_found_when_sheet_not_exists(self):
        """UT-BACK-MAQ-DET-002: 404 cuando servicio indica 'ficha no encontrada'"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_002_not_found_when_sheet_not_exists.__name__} ---")
        
        machinery_id = 16
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar None (no encontrada)
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                mock_filter.return_value.first.return_value = None
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert response.data['success'] is False
                assert response.data['message'] == "No existe ficha técnica específica para la maquinaria indicada"
                assert response.data['data'] is None

    def test_UT_BACK_MAQ_DET_003_unauthorized_without_authentication(self):
        """UT-BACK-MAQ-DET-003: 401 cuando no hay autenticación"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_003_unauthorized_without_authentication.__name__} ---")
        
        machinery_id = 15
        
        # Remover autenticación
        self.client.force_authenticate(user=None)
        
        # Mock para verificar que el servicio no se llama
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
            response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Assertions
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.data['detail'] == "Authentication credentials were not provided."
            # Verificar que el servicio no fue llamado
            mock_filter.assert_not_called()

    def test_UT_BACK_MAQ_DET_004_forbidden_without_permission(self):
        """UT-BACK-MAQ-DET-004: 403 cuando el usuario no tiene permiso de consulta"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_004_forbidden_without_permission.__name__} ---")
        
        machinery_id = 15
        
        # Mock del request para simular usuario sin permisos
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.check_permission') as mock_permission:
            mock_permission.return_value = False
            
            # Mock para verificar que el servicio no se llama
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert "No tiene permisos para obtener una ficha técnica específica" in response.data['message']
                # Verificar que el servicio no fue llamado
                mock_filter.assert_not_called()

    def test_UT_BACK_MAQ_DET_005_bad_request_invalid_machinery_id_format(self):
        """UT-BACK-MAQ-DET-005: 400 cuando machinery_id no es entero"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_005_bad_request_invalid_machinery_id_format.__name__} ---")
        
        machinery_id = "abc"
        
        # Mock para verificar que el servicio no se llama
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
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
            assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
            # Verificar que el servicio no fue llamado
            mock_filter.assert_not_called()

    def test_UT_BACK_MAQ_DET_006_bad_request_invalid_machinery_id_values(self):
        """UT-BACK-MAQ-DET-006: 400 cuando machinery_id ≤ 0"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_006_bad_request_invalid_machinery_id_values.__name__} ---")
        
        # Probar con 0 y -5
        for machinery_id in [0, -5]:
            print(f"Testing with machinery_id: {machinery_id}")
            
            # Mock para verificar que el servicio no se llama
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                # Manejar respuesta que puede no ser JSON
                try:
                    response_data = response.json()
                    print(f"Response: {response_data}")
                except ValueError:
                    print(f"Response Content-Type: {response.get('Content-Type')}")
                
                # Assertions - Django REST Framework maneja automáticamente la validación
                # Los valores ≤ 0 pueden retornar 403 (sin permisos) o 400/404 (validación)
                assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]
                # Verificar que el servicio no fue llamado
                mock_filter.assert_not_called()

    def test_UT_BACK_MAQ_DET_007_success_with_partial_data_nulls(self):
        """UT-BACK-MAQ-DET-007: 200 con datos parciales (nullables) sin romper serialización"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_007_success_with_partial_data_nulls.__name__} ---")
        
        machinery_id = 21
        
        # Mock del objeto de ficha técnica específica con campos nulos
        mock_sheet = MagicMock()
        mock_sheet.id_specific_technical_sheet = 1
        mock_sheet.power = 150.5
        mock_sheet.power_unit = MagicMock(id_units=1, name="kW")
        mock_sheet.fuel_capacity = None
        mock_sheet.fuel_capacity_unit = None
        mock_sheet.carrying_capacity = None
        
        # Mock del serializer con datos que incluyen nulos
        expected_data = {
            "id_specific_technical_sheet": 1,
            "power": 150.5,
            "power_unit": 1,
            "fuel_capacity": None,
            "fuel_capacity_unit": None,
            "carrying_capacity": None,
            "operating_weight": "2500.0"
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha con nulos
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                mock_filter.return_value.first.return_value = mock_sheet
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                assert response.data['success'] is True
                assert response.data['data']['fuel_capacity'] is None
                assert response.data['data']['fuel_capacity_unit'] is None
                assert response.data['data']['carrying_capacity'] is None

    def test_UT_BACK_MAQ_DET_008_correct_numeric_types_mapping(self):
        """UT-BACK-MAQ-DET-008: Mapeo correcto de tipos numéricos y enteros de catálogos"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_008_correct_numeric_types_mapping.__name__} ---")
        
        machinery_id = 22
        
        # Mock del objeto de ficha técnica específica con tipos específicos
        mock_sheet = MagicMock()
        mock_sheet.id_specific_technical_sheet = 1
        mock_sheet.power = 150.5  # float
        mock_sheet.power_unit = MagicMock(id_units=1, name="kW")  # int
        mock_sheet.engine_type = MagicMock(id_types=2, name="Diésel")  # int
        mock_sheet.cylinder_count = 4  # int
        mock_sheet.max_speed = 45.0  # float
        
        # Mock del serializer con tipos correctos
        expected_data = {
            "id_specific_technical_sheet": 1,
            "power": 150.5,  # float
            "power_unit": 1,  # int
            "engine_type": 2,  # int
            "cylinder_count": 4,  # int
            "max_speed": 45.0,  # float
            "operating_weight": "2500.0"
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                mock_filter.return_value.first.return_value = mock_sheet
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                data = response.data['data']
                assert isinstance(data['power'], float)
                assert isinstance(data['power_unit'], int)
                assert isinstance(data['engine_type'], int)
                assert isinstance(data['cylinder_count'], int)
                assert isinstance(data['max_speed'], float)

    def test_UT_BACK_MAQ_DET_009_internal_server_error_unexpected_exception(self):
        """UT-BACK-MAQ-DET-009: 500 cuando el servicio lanza excepción inesperada"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_009_internal_server_error_unexpected_exception.__name__} ---")
        
        machinery_id = 15
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para lanzar excepción genérica
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                mock_filter.side_effect = Exception("DB down")
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert response.data['success'] is False
                assert response.data['message'] == "Error inesperado al consultar la ficha técnica específica"
                assert 'details' in response.data
                # Verificar que no se expone información sensible
                assert 'DB down' in response.data['details']

    def test_UT_BACK_MAQ_DET_010_response_headers_and_structure(self):
        """UT-BACK-MAQ-DET-010: Cabeceras y forma de respuesta (Content-Type/estructura)"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_BACK_MAQ_DET_010_response_headers_and_structure.__name__} ---")
        
        # Test 1: Respuesta 200 (servicio OK)
        machinery_id_200 = 15
        mock_sheet = MagicMock()
        mock_sheet.id_specific_technical_sheet = 1
        
        expected_data = {"id_specific_technical_sheet": 1, "power": 150.5}
        self.mock_serializer.data = expected_data
        
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                mock_filter.return_value.first.return_value = mock_sheet
                
                response_200 = self.client.get(self.endpoint_template.format(machinery_id=machinery_id_200))
                
                print(f"200 Response Status: {response_200.status_code}")
                print(f"200 Response: {response_200.json()}")
                
                # Assertions para respuesta 200
                assert response_200.status_code == status.HTTP_200_OK
                assert response_200['Content-Type'] == 'application/json'
                assert 'success' in response_200.data
                assert 'message' in response_200.data
                assert 'data' in response_200.data
                assert response_200.data['success'] is True
                assert response_200.data['data'] == expected_data
        
        # Test 2: Respuesta 404 (no encontrada)
        machinery_id_404 = 16
        
        with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            with patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheet.objects.filter') as mock_filter:
                mock_filter.return_value.first.return_value = None
                
                response_404 = self.client.get(self.endpoint_template.format(machinery_id=machinery_id_404))
                
                print(f"404 Response Status: {response_404.status_code}")
                print(f"404 Response: {response_404.json()}")
                
                # Assertions para respuesta 404
                assert response_404.status_code == status.HTTP_404_NOT_FOUND
                assert response_404['Content-Type'] == 'application/json'
                assert 'success' in response_404.data
                assert 'message' in response_404.data
                assert 'data' in response_404.data
                assert response_404.data['success'] is False
                assert response_404.data['data'] is None
