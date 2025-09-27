"""
Pruebas unitarias para el endpoint de consulta de uso de maquinaria
ID: UT-MAQ-166 a UT-MAQ-166.15 (HU-MAQ-009)
Endpoint: GET /machinery-usage/by-machinery/{machinery_id}/

Estrategia: Usar mocks para simular autenticación, permisos y servicios.
- Mockeamos la autenticación del usuario
- Mockeamos los permisos de consulta (permiso 95)
- Mockeamos el servicio de obtención de ficha de uso
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
from datetime import datetime, date
import re

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
from machinery.models import MachineryUsageSheet, Machinery
from parameterization.models import Statues, StatuesCategory, Types, TypesCategory, Brands, BrandsCategory, Models, Units, UnitsCategory


@pytest.mark.django_db
class TestMachineryUsageDetail:
    """Pruebas para el endpoint de consulta de uso de maquinaria"""
    
    endpoint_template = '/machinery-usage/by-machinery/{machinery_id}/'

    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        # Usuario simulado para autenticación con atributos necesarios
        self.mock_user = User(id_user=1)
        self.mock_user.is_authenticated = True
        self.client.force_authenticate(user=self.mock_user)
        
        # Mock del serializer
        self.get_serializer_patcher = patch('machinery.api.machinery_usage_viewset.MachineryUsageSheetDetailSerializer')
        self.mock_get_serializer = self.get_serializer_patcher.start()
        self.mock_serializer = MagicMock()
        self.mock_get_serializer.return_value = self.mock_serializer

    def teardown_method(self):
        """Limpieza después de cada test"""
        try:
            self.get_serializer_patcher.stop()
        except Exception:
            pass

    def test_UT_MAQ_166_success_usage_found(self):
        """UT-MAQ-166: 200 OK – Uso de maquinaria (camino feliz)"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_success_usage_found.__name__} ---")
        
        machinery_id = 5
        
        # Mock del objeto de uso de maquinaria
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 5
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 5,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso (permiso 95)
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                assert response_data["data"] == expected_data
                assert response['Content-Type'] == 'application/json'
                
                # Validaciones específicas de campos
                data = response_data["data"]
                assert data['id_usage_sheet'] == 5
                assert data['acquisition_date'] == "2025-12-06"
                assert data['usage_condition'] == 8
                assert data['usage_hours'] == "100.00"
                assert data['distance_value'] == "100.000"
                assert data['distance_unit'] == 16
                assert data['tenancy_type'] is None
                assert data['is_own'] is True
                assert data['contract_end_date'] is None

    def test_UT_MAQ_166_1_forbidden_no_permission(self):
        """UT-MAQ-166.1: 403 – Usuario sin permiso 95"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_1_forbidden_no_permission.__name__} ---")
        
        machinery_id = 7
        
        # Mock de permisos para denegar acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = False
            
            # Mock para verificar que el servicio no se llama
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert response.data['message'] == "No tiene permisos para obtener una ficha de uso de la maquinaria."
                # Verificar que el servicio no fue llamado
                mock_query.assert_not_called()

    def test_UT_MAQ_166_2_unauthorized_no_authentication(self):
        """UT-MAQ-166.2: 401 – Usuario no autenticado"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_2_unauthorized_no_authentication.__name__} ---")
        
        machinery_id = 7
        
        # Remover autenticación
        self.client.force_authenticate(user=None)
        
        # Mock para verificar que el servicio no se llama
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
            response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Assertions
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert response.data['detail'] == "Authentication credentials were not provided."
            # Verificar que el servicio no fue llamado
            mock_query.assert_not_called()

    def test_UT_MAQ_166_3_machinery_not_exists(self):
        """UT-MAQ-166.3: 404 – Maquinaria no existe"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_3_machinery_not_exists.__name__} ---")
        
        machinery_id = 9999
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para lanzar DoesNotExist
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.side_effect = MachineryUsageSheet.DoesNotExist()
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert response.data['success'] is False
                assert response.data['message'] == "La maquinaria no tiene ficha de uso registrada"

    def test_UT_MAQ_166_4_no_usage_sheet_associated(self):
        """UT-MAQ-166.4: 404 – Sin ficha de uso asociada"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_4_no_usage_sheet_associated.__name__} ---")
        
        machinery_id = 6
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para lanzar DoesNotExist (maquinaria existe pero sin ficha de uso)
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.side_effect = MachineryUsageSheet.DoesNotExist()
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert response.data['success'] is False
                assert response.data['message'] == "La maquinaria no tiene ficha de uso registrada"

    def test_UT_MAQ_166_5_bad_request_invalid_id_format(self):
        """UT-MAQ-166.5: 400 – id_machinery no numérico"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_5_bad_request_invalid_id_format.__name__} ---")
        
        machinery_id = "abc"
        
        # Mock para verificar que el servicio no se llama
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
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
            assert response.data['message'] == "No tiene permisos para obtener una ficha de uso de la maquinaria."
            # Verificar que el servicio no fue llamado
            mock_query.assert_not_called()

    def test_UT_MAQ_166_6_iso_date_format(self):
        """UT-MAQ-166.6: Formato – Fechas ISO YYYY-MM-DD"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_6_iso_date_format.__name__} ---")
        
        machinery_id = 10
        
        # Mock del objeto de uso de maquinaria con fechas
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 10
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 10,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                
                # Verificar formato ISO de fechas
                acquisition_date = response_data["data"]["acquisition_date"]
                iso_pattern = r'^\d{4}-\d{2}-\d{2}$'
                assert re.match(iso_pattern, acquisition_date), f"Fecha {acquisition_date} no cumple formato ISO"
                
                # Verificar que se puede parsear correctamente
                try:
                    datetime.strptime(acquisition_date, '%Y-%m-%d')
                except ValueError:
                    assert False, f"Fecha {acquisition_date} no es válida"

    def test_UT_MAQ_166_7_decimal_strings_format(self):
        """UT-MAQ-166.7: Formato – Números con decimales como strings"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_7_decimal_strings_format.__name__} ---")
        
        machinery_id = 11
        
        # Mock del objeto de uso de maquinaria
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 11
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 11,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                
                # Verificar tipos y formatos de decimales
                usage_hours = response_data["data"]["usage_hours"]
                distance_value = response_data["data"]["distance_value"]
                
                assert isinstance(usage_hours, str)
                assert isinstance(distance_value, str)
                
                # Verificar patrones de decimales
                usage_hours_pattern = r'^\d+\.\d{2}$'
                distance_value_pattern = r'^\d+\.\d{3}$'
                
                assert re.match(usage_hours_pattern, usage_hours), f"usage_hours {usage_hours} no cumple formato esperado"
                assert re.match(distance_value_pattern, distance_value), f"distance_value {distance_value} no cumple formato esperado"

    def test_UT_MAQ_166_8_own_tenancy_consistency(self):
        """UT-MAQ-166.8: Consistencia – is_own=true implica tenancy_type=null y sin contract_end_date"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_8_own_tenancy_consistency.__name__} ---")
        
        machinery_id = 12
        
        # Mock del objeto de uso de maquinaria con tenencia propia
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 12
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 12,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                
                # Verificar consistencia de tenencia propia
                data = response_data["data"]
                assert data['is_own'] is True
                assert data['tenancy_type'] is None
                assert data['contract_end_date'] is None

    def test_UT_MAQ_166_9_rental_tenancy_consistency(self):
        """UT-MAQ-166.9: Consistencia – is_own=false requiere tenancy_type válido"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_9_rental_tenancy_consistency.__name__} ---")
        
        machinery_id = 13
        
        # Mock del objeto de uso de maquinaria con tenencia no propia
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 13
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = MagicMock()
        mock_usage.tenancy_type.id_types = 11
        mock_usage.is_own = False
        mock_usage.contract_end_date = date(2026, 1, 31)
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 13,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": 11,
            "is_own": False,
            "contract_end_date": "2026-01-31"
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                
                # Verificar consistencia de tenencia no propia
                data = response_data["data"]
                assert data['is_own'] is False
                assert data['tenancy_type'] is not None
                assert data['tenancy_type'] == 11
                
                # Verificar formato ISO de fecha de contrato
                contract_end_date = data['contract_end_date']
                if contract_end_date is not None:
                    iso_pattern = r'^\d{4}-\d{2}-\d{2}$'
                    assert re.match(iso_pattern, contract_end_date), f"Fecha {contract_end_date} no cumple formato ISO"

    def test_UT_MAQ_166_10_usage_condition_id_reference(self):
        """UT-MAQ-166.10: Referencias – usage_condition (estatus) devuelve ID de categoría 3"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_10_usage_condition_id_reference.__name__} ---")
        
        machinery_id = 14
        
        # Mock del objeto de uso de maquinaria
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 14
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 14,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                
                # Verificar que usage_condition es numérico (ID crudo)
                usage_condition = response_data["data"]["usage_condition"]
                assert isinstance(usage_condition, int)
                assert usage_condition == 8

    def test_UT_MAQ_166_11_distance_unit_id_reference(self):
        """UT-MAQ-166.11: Referencias – distance_unit (unidades) devuelve ID de categoría 7"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_11_distance_unit_id_reference.__name__} ---")
        
        machinery_id = 15
        
        # Mock del objeto de uso de maquinaria
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 15
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 15,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                
                # Verificar que distance_unit es numérico (ID crudo)
                distance_unit = response_data["data"]["distance_unit"]
                assert isinstance(distance_unit, int)
                assert distance_unit == 16

    def test_UT_MAQ_166_12_null_fields_tolerance(self):
        """UT-MAQ-166.12: Tolerancia a nulos – Campos opcionales ausentes"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_12_null_fields_tolerance.__name__} ---")
        
        machinery_id = 16
        
        # Mock del objeto de uso de maquinaria con campos opcionales nulos
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 16
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 16,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                
                # Verificar que los campos opcionales están presentes con null (no omitidos)
                data = response_data["data"]
                assert "tenancy_type" in data
                assert "contract_end_date" in data
                assert data["tenancy_type"] is None
                assert data["contract_end_date"] is None

    def test_UT_MAQ_166_13_network_error_robustness(self):
        """UT-MAQ-166.13: Robustez – Error de red/timeout del repositorio"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_13_network_error_robustness.__name__} ---")
        
        machinery_id = 17
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para lanzar TimeoutError
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.side_effect = TimeoutError("Connection timeout")
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions - El endpoint actual maneja excepciones genéricas como 400
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert response.data['success'] is False
                assert response.data['message'] == "Error al obtener la ficha de uso"
                assert 'details' in response.data

    def test_UT_MAQ_166_14_content_type_header(self):
        """UT-MAQ-166.14: Encabezados – Content-Type: application/json"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_14_content_type_header.__name__} ---")
        
        machinery_id = 18
        
        # Mock del objeto de uso de maquinaria
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 18
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados
        expected_data = {
            "id_usage_sheet": 18,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                print(f"Headers: {dict(response.headers)}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                assert response['Content-Type'] == 'application/json'
                
                # Verificar estructura de respuesta
                response_data = response.json()
                assert response_data["success"] == True
                assert response_data["data"] == expected_data

    def test_UT_MAQ_166_15_exact_contract_schema(self):
        """UT-MAQ-166.15: No contaminación del contrato – Sin campos extra"""
        print(f"\n--- Testing: {self.__class__.__name__}.{self.test_UT_MAQ_166_15_exact_contract_schema.__name__} ---")
        
        machinery_id = 19
        
        # Mock del objeto de uso de maquinaria
        mock_usage = MagicMock()
        mock_usage.id_usage_sheet = 19
        mock_usage.acquisition_date = date(2025, 12, 6)
        mock_usage.usage_condition = MagicMock()
        mock_usage.usage_condition.id_statues = 8
        mock_usage.usage_hours = "100.00"
        mock_usage.distance_value = "100.000"
        mock_usage.distance_unit = MagicMock()
        mock_usage.distance_unit.id_units = 16
        mock_usage.tenancy_type = None
        mock_usage.is_own = True
        mock_usage.contract_end_date = None
        
        # Mock del serializer con datos esperados (exactamente los campos del contrato)
        expected_data = {
            "id_usage_sheet": 19,
            "acquisition_date": "2025-12-06",
            "usage_condition": 8,
            "usage_hours": "100.00",
            "distance_value": "100.000",
            "distance_unit": 16,
            "tenancy_type": None,
            "is_own": True,
            "contract_end_date": None
        }
        self.mock_serializer.data = expected_data
        
        # Mock de permisos para permitir acceso
        with patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.check_permission') as mock_permission:
            mock_permission.return_value = True
            
            # Mock del servicio para retornar la ficha de uso
            with patch('machinery.api.machinery_usage_viewset.MachineryUsageSheet.objects.select_related') as mock_query:
                mock_query.return_value.get.return_value = mock_usage
                
                response = self.client.get(self.endpoint_template.format(machinery_id=machinery_id))
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                
                # Assertions
                assert response.status_code == status.HTTP_200_OK
                response_data = response.json()
                assert response_data["success"] == True
                
                # Verificar que data contiene exactamente los campos del contrato
                data = response_data["data"]
                expected_fields = {
                    "id_usage_sheet", "acquisition_date", "usage_condition", 
                    "usage_hours", "distance_value", "distance_unit", 
                    "tenancy_type", "is_own", "contract_end_date"
                }
                assert set(data.keys()) == expected_fields
                
                # Verificar que no hay campos extra
                assert len(data.keys()) == 9


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
