import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework import serializers as drf_serializers


class TestSpecificTechnicalSheetCreation(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/machinery-specific-sheet/'
        self.valid_data = {
            "machinery_id": 1,
            "power": 100.0,
            "power_unit": "kW",
            "category": "Excavadora",
            "subcategory": "Excavadora Hidráulica",
            "brand": "Caterpillar",
            "model": "320D",
            "serial_number": "CAT123456",
            "year": 2020,
            "working_hours": 1500,
            "location": "Sitio A",
            "status": "Operativo",
            "fuel_type": "Diésel",
            "fuel_capacity": 200.0,
            "fuel_unit": "litros",
            "engine_brand": "Caterpillar",
            "engine_model": "C7.1",
            "transmission_type": "Hidráulica",
            "tires_brand": "Michelin",
            "tires_model": "XHA2",
            "tires_quantity": 4,
            "tires_size": "20.5R25",
            "tracks_brand": None,
            "tracks_model": None,
            "tracks_quantity": None,
            "tracks_size": None,
            "hydraulic_system_brand": "Bosch Rexroth",
            "hydraulic_system_model": "A10V",
            "attachments": "Cuchara, Martillo",
            "observations": "Maquinaria en buen estado",
            "maintenance_schedule": "Cada 500 horas",
            "safety_features": "Cabina ROPS/FOPS",
            "operator_manual": "Disponible",
            "technical_sheet_url": "https://example.com/sheet.pdf",
            "images": ["https://example.com/image1.jpg"],
            "videos": [],
            "documents": []
        }

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_1(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.return_value = True
        mock_instance.validated_data = self.valid_data
        mock_instance.save.return_value = MagicMock()
        mock_instance.data = self.valid_data
        mock_get_serializer.return_value = mock_instance

        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_2(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.side_effect = drf_serializers.ValidationError({'machinery_id': ['Este campo es requerido.']})
        mock_get_serializer.return_value = mock_instance

        data = self.valid_data.copy()
        del data['machinery_id']
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('machinery_id', response.data.get('errors', {}) or response.data)

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_3(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.side_effect = drf_serializers.ValidationError({'power': ['La potencia debe ser mayor a 0.']})
        mock_get_serializer.return_value = mock_instance

        data = self.valid_data.copy()
        data['power'] = 0
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('power', response.data.get('errors', {}) or response.data)

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_4(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.side_effect = drf_serializers.ValidationError({'category': ['Categoría inválida.']})
        mock_get_serializer.return_value = mock_instance

        data = self.valid_data.copy()
        data['category'] = 'InvalidCategory'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data.get('errors', {}) or response.data)

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_5(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.side_effect = drf_serializers.ValidationError({'subcategory': ['Subcategoría inválida para la categoría seleccionada.']})
        mock_get_serializer.return_value = mock_instance

        data = self.valid_data.copy()
        data['subcategory'] = 'InvalidSubcategory'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('subcategory', response.data.get('errors', {}) or response.data)

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_6(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.side_effect = drf_serializers.ValidationError({'brand': ['Este campo es requerido.']})
        mock_get_serializer.return_value = mock_instance

        data = self.valid_data.copy()
        del data['brand']
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('brand', response.data.get('errors', {}) or response.data)

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_7(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.side_effect = drf_serializers.ValidationError({'year': ['El año debe estar entre 1900 y el año actual.']})
        mock_get_serializer.return_value = mock_instance

        data = self.valid_data.copy()
        data['year'] = 1800
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('year', response.data.get('errors', {}) or response.data)

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_8(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.side_effect = drf_serializers.ValidationError({'working_hours': ['Las horas de trabajo deben ser mayores o iguales a 0.']})
        mock_get_serializer.return_value = mock_instance

        data = self.valid_data.copy()
        data['working_hours'] = -1
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('working_hours', response.data.get('errors', {}) or response.data)

    @patch('machinery.api.machinery_specific_sheet_viewset.SpecificTechnicalSheetViewSet.get_serializer')
    def test_ut_maq_003_9(self, mock_get_serializer):
        mock_instance = MagicMock()
        mock_instance.is_valid.side_effect = drf_serializers.ValidationError({'fuel_capacity': ['La capacidad de combustible debe ser mayor a 0.']})
        mock_get_serializer.return_value = mock_instance

        data = self.valid_data.copy()
        data['fuel_capacity'] = 0
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fuel_capacity', response.data.get('errors', {}) or response.data)


if __name__ == '__main__':
    unittest.main()
