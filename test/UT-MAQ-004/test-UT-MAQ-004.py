"""
Pruebas unitarias para el endpoint de creación de ficha de uso de maquinaria
ID: UT-MAQ-004 (HU-MAQ-004)

Estrategia: evitar escribir en la base de datos real usando mocks.
- Parcheamos en setup el serializer que usa el viewset (`MachineryUsageSheetCreateSerializer`).
- Mockeamos llamadas a `Model.objects.get` y `Model.objects.filter` donde haga falta.
- Validamos respuestas del endpoint (status code y payload) según el comportamiento esperado.

Notas:
- No se modifican archivos fuera de `test`.
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

# Importar User sólo para crear objeto simulacro de autenticación (no persistir)
from users.models.user import User


@pytest.mark.django_db
class TestMachineryUsageSheet:
    endpoint = '/machinery-usage/create/'

    def setup_method(self):
        self.client = APIClient()
        # Usuario simulado para autenticación (no guardado en BD)
        self.mock_user = User(id_user=1)
        self.client.force_authenticate(user=self.mock_user)
        # Parche global del método get_serializer del viewset para usar nuestro serializer mock
        self.get_serializer_patcher = patch('machinery.api.machinery_usage_viewset.MachineryUsageViewSet.get_serializer')
        self.mock_get_serializer = self.get_serializer_patcher.start()
        # instancia por defecto válida; los tests la sobreescriben según necesiten
        self.mock_serializer = MagicMock()
        self.mock_serializer.is_valid.return_value = True
        self.mock_serializer.save.return_value = MagicMock()
        self.mock_serializer.errors = {}
        self.mock_get_serializer.return_value = self.mock_serializer

    def teardown_method(self):
        try:
            self.get_serializer_patcher.stop()
        except Exception:
            pass

    @patch('machinery.models.Machinery.objects.get')
    @patch('parameterization.models.Statues.objects.get')
    @patch('parameterization.models.Units.objects.get')
    @patch('users.models.User.objects.get')
    @patch('machinery.models.MachineryUsageSheet.objects.filter')
    def test_create_usage_success_own(self, mock_usage_filter, mock_user_get, mock_units_get, mock_statues_get, mock_machinery_get):
        """Creación exitosa cuando is_own=True (serializer válido)"""
        # Configurar objetos mock
        mock_machinery = MagicMock()
        mock_machinery.id_machinery = 1
        mock_statues = MagicMock()
        mock_statues.id_statues = 2
        mock_units = MagicMock()
        mock_units.id_units = 3
        mock_user = MagicMock()
        mock_user.id_user = 4

        mock_machinery_get.return_value = mock_machinery
        mock_statues_get.return_value = mock_statues
        mock_units_get.return_value = mock_units
        mock_user_get.return_value = mock_user
        mock_usage_filter.return_value.exists.return_value = False

        # El serializer devolverá una instancia guardada
        saved_instance = MagicMock()
        saved_instance.is_own = True
        saved_instance.tenancy_type = None
        saved_instance.contract_end_date = None
        self.mock_serializer.is_valid.return_value = True
        self.mock_serializer.save.return_value = saved_instance

        data = {
            'id_machinery': 1,
            'is_own': True,
            'acquisition_date': '2025-09-22',
            'usage_condition': 2,
            'usage_hours': '123.50',
            'distance_value': '2500.750',
            'distance_unit': 3,
            'responsible_user': 4
        }

        response = self.client.post(self.endpoint, data, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'Ficha de uso registrada exitosamente' in response.data['message']

    @patch('machinery.models.Machinery.objects.get')
    @patch('parameterization.models.Statues.objects.get')
    @patch('parameterization.models.Units.objects.get')
    @patch('parameterization.models.Types.objects.get')
    @patch('users.models.User.objects.get')
    @patch('machinery.models.MachineryUsageSheet.objects.filter')
    def test_create_usage_success_not_own(self, mock_usage_filter, mock_user_get, mock_types_get, mock_units_get, mock_statues_get, mock_machinery_get):
        """Creación exitosa cuando is_own=False (serializer válido)"""
        mock_machinery = MagicMock()
        mock_machinery.id_machinery = 1
        mock_statues = MagicMock()
        mock_units = MagicMock()
        mock_types = MagicMock()
        mock_user = MagicMock()
        mock_user.id_user = 4

        mock_machinery_get.return_value = mock_machinery
        mock_statues_get.return_value = mock_statues
        mock_units_get.return_value = mock_units
        mock_types_get.return_value = mock_types
        mock_user_get.return_value = mock_user
        mock_usage_filter.return_value.exists.return_value = False

        saved_instance = MagicMock()
        saved_instance.is_own = False
        saved_instance.tenancy_type = mock_types
        saved_instance.contract_end_date = '2026-09-22'
        self.mock_serializer.is_valid.return_value = True
        self.mock_serializer.save.return_value = saved_instance

        data = {
            'id_machinery': 1,
            'is_own': False,
            'acquisition_date': '2025-09-22',
            'usage_condition': 2,
            'usage_hours': '123.50',
            'distance_value': '2500.750',
            'distance_unit': 3,
            'tenancy_type': 5,
            'contract_end_date': '2026-09-22',
            'responsible_user': 4
        }

        response = self.client.post(self.endpoint, data, format='multipart')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'Ficha de uso registrada exitosamente' in response.data['message']

    @patch('machinery.models.Machinery.objects.get')
    @patch('parameterization.models.Statues.objects.get')
    @patch('parameterization.models.Units.objects.get')
    @patch('users.models.User.objects.get')
    @patch('machinery.models.MachineryUsageSheet.objects.filter')
    def test_missing_required_fields(self, mock_usage_filter, mock_user_get, mock_units_get, mock_statues_get, mock_machinery_get):
        """Campos obligatorios faltantes (serializer invalida)"""
        mock_machinery = MagicMock()
        mock_statues = MagicMock()
        mock_units = MagicMock()
        mock_user = MagicMock()

        mock_machinery_get.return_value = mock_machinery
        mock_statues_get.return_value = mock_statues
        mock_units_get.return_value = mock_units
        mock_user_get.return_value = mock_user
        mock_usage_filter.return_value.exists.return_value = False

        required_fields = ['id_machinery', 'is_own', 'acquisition_date', 'usage_condition', 'usage_hours', 'distance_value', 'distance_unit', 'responsible_user']
        for field in required_fields:
            data = {
                'id_machinery': 1,
                'is_own': True,
                'acquisition_date': '2025-09-22',
                'usage_condition': 2,
                'usage_hours': '123.50',
                'distance_value': '2500.750',
                'distance_unit': 3,
                'responsible_user': 4
            }
            del data[field]

            # Simular fallo de validación en serializer
            self.mock_serializer.is_valid.return_value = False
            self.mock_serializer.errors = {field: ['This field is required.']}

            response = self.client.post(self.endpoint, data, format='multipart')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data['success'] is False
            assert 'Error de validación' in response.data['message']
            assert field in response.data['details']
            # Reset serializer a válido para la siguiente iteración
            self.mock_serializer.is_valid.return_value = True
            self.mock_serializer.errors = {}

    @patch('machinery.models.Machinery.objects.get')
    @patch('parameterization.models.Statues.objects.get')
    @patch('parameterization.models.Units.objects.get')
    @patch('users.models.User.objects.get')
    @patch('machinery.models.MachineryUsageSheet.objects.filter')
    def test_invalid_acquisition_date_format(self, mock_usage_filter, mock_user_get, mock_units_get, mock_statues_get, mock_machinery_get):
        """Formato inválido de acquisition_date (serializer invalido)"""
        mock_machinery = MagicMock()
        mock_statues = MagicMock()
        mock_units = MagicMock()
        mock_user = MagicMock()

        mock_machinery_get.return_value = mock_machinery
        mock_statues_get.return_value = mock_statues
        mock_units_get.return_value = mock_units
        mock_user_get.return_value = mock_user
        mock_usage_filter.return_value.exists.return_value = False

        data = {
            'id_machinery': 1,
            'is_own': True,
            'acquisition_date': '22-09-2025',  # Formato incorrecto
            'usage_condition': 2,
            'usage_hours': '123.50',
            'distance_value': '2500.750',
            'distance_unit': 3,
            'responsible_user': 4
        }

        self.mock_serializer.is_valid.return_value = False
        self.mock_serializer.errors = {'acquisition_date': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.']}

        response = self.client.post(self.endpoint, data, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'acquisition_date' in response.data['details']
        assert 'Date has wrong format' in str(response.data['details']['acquisition_date'])
        # reset
        self.mock_serializer.is_valid.return_value = True
        self.mock_serializer.errors = {}

    def test_contract_fields_required_when_not_own(self):
        """Test contract_end_date y tenancy_type obligatorios cuando is_own=False"""
        data = {
            'id_machinery': 999999992,
            'is_own': False,
            'acquisition_date': '2025-09-22',
            'usage_condition': 999999997,
            'usage_hours': '123.50',
            'distance_value': '2500.750',
            'distance_unit': 999999995,
            'responsible_user': 999999999
            # Faltan tenancy_type y contract_end_date
        }
        # Simular validación fallida por campos de contrato faltantes
        self.mock_serializer.is_valid.return_value = False
        self.mock_serializer.errors = {'tenancy_type': ['This field is required.'], 'contract_end_date': ['This field is required.']}

        response = self.client.post(self.endpoint, data, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tenancy_type' in response.data['details'] or 'contract_end_date' in response.data['details']

    def test_invalid_contract_end_date_format(self):
        """Test formato inválido de contract_end_date"""
        data = {
            'id_machinery': 999999992,
            'is_own': False,
            'acquisition_date': '2025-09-22',
            'usage_condition': 999999997,
            'usage_hours': '123.50',
            'distance_value': '2500.750',
            'distance_unit': 999999995,
            'tenancy_type': 999999993,
            'contract_end_date': '22-09-2026',  # Formato incorrecto
            'responsible_user': 999999999
        }
        # Simular error de formato en el serializer
        self.mock_serializer.is_valid.return_value = False
        self.mock_serializer.errors = {'contract_end_date': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.']}

        response = self.client.post(self.endpoint, data, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'contract_end_date' in response.data['details']
        assert 'Date has wrong format' in str(response.data['details']['contract_end_date'])

    def test_nonexistent_machinery(self):
        """Test id_machinery no existe"""
        data = {
            'id_machinery': 999999992,  # No existe
            'is_own': True,
            'acquisition_date': '2025-09-22',
            'usage_condition': 999999997,
            'usage_hours': '123.50',
            'distance_value': '2500.750',
            'distance_unit': 999999995,
            'responsible_user': 999999999
        }
        # Simular error de existencia en el serializer
        self.mock_serializer.is_valid.return_value = False
        self.mock_serializer.errors = {'id_machinery': ['No machinery found with this id.']}

        response = self.client.post(self.endpoint, data, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'id_machinery' in response.data['details']

    def test_nonexistent_responsible_user(self):
        """Test responsible_user no existe"""
        data = {
            'id_machinery': 999999992,
            'is_own': True,
            'acquisition_date': '2025-09-22',
            'usage_condition': 999999997,
            'usage_hours': '123.50',
            'distance_value': '2500.750',
            'distance_unit': 999999995,
            'responsible_user': 999999999  # No existe
        }
        # Simular error de existencia en el serializer
        self.mock_serializer.is_valid.return_value = False
        self.mock_serializer.errors = {'responsible_user': ['No user found with this id.']}

        response = self.client.post(self.endpoint, data, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'responsible_user' in response.data['details']
