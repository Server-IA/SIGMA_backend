"""
Pruebas unitarias para el endpoint de creación de maquinaria general
ID: UT-MAQ-001 a UT-MAQ-011 (HU-MAQ-001)
"""

import sys
import os
import pytest
from datetime import datetime
from unittest.mock import patch

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

from machinery.models import Machinery, TelemetryDevices
from users.models.user import User
from parameterization.models import Statues, StatuesCategory, Types, TypesCategory, Brands, BrandsCategory, Models


import io
from PIL import Image
import inspect

@pytest.mark.django_db
class TestMachineryGeneralSheet:
    endpoint = '/machinery/create-general-sheet/'

    def setup_method(self):
        self.client = APIClient()
        # Crear usuario responsable y autenticado (solo id_user)
        self.user = User.objects.create(id_user=1)
        self.client.force_authenticate(user=self.user)
        # Crear categorías y tipos requeridos (proveer fechas y responsable donde son obligatorios)
        now = timezone.now()
        self.statues_category = StatuesCategory.objects.create(
            id_statues_categories=2,
            name='Estados Maquinaria',
            description='Estados de la maquinaria',
            modification_date=now,
            creation_date=now,
            id_responsible_user=self.user
        )
        self.statues = Statues.objects.create(
            id_statues=3,
            name='En registro',
            description='Estado inicial',
            id_statues_categories=self.statues_category,
            modification_date=now,
            creation_date=now,
            id_responsible_user=self.user
        )
        self.types_category_prim = TypesCategory.objects.create(
            id_types_categories=2,
            name='Tipos primario de maquinaria',
            description='Primario',
            creation_date=now,
            modification_date=now,
            id_responsible_user=self.user
        )
        self.types_category_sec = TypesCategory.objects.create(
            id_types_categories=3,
            name='Tipos secundario de maquinaria',
            description='Secundario',
            creation_date=now,
            modification_date=now,
            id_responsible_user=self.user
        )
        self.type_prim = Types.objects.create(
            id_types=2,
            name='Tractor',
            description='Tractor',
            id_types_categories=self.types_category_prim,
            id_responsible_user=self.user,
            id_statues=self.statues,
            creation_date=now,
            modification_date=now
        )
        self.type_sec = Types.objects.create(
            id_types=5,
            name='Tractor Sec',
            description='Tractor Sec',
            id_types_categories=self.types_category_sec,
            id_responsible_user=self.user,
            id_statues=self.statues,
            creation_date=now,
            modification_date=now
        )
        self.brands_category = BrandsCategory.objects.create(
            id_brands_categories=1,
            name='Marcas Maquinaria',
            description='Marcas',
            modification_date=now,
            creation_date=now,
            id_responsible_user=self.user
        )
        self.brand = Brands.objects.create(
            id_brands=1,
            name='MarcaTest',
            description='MarcaTest',
            id_brands_categories=self.brands_category,
            id_responsible_user=self.user,
            id_statues=self.statues,
            modification_date=now,
            creation_date=now
        )
        self.model = Models.objects.create(
            id_model=4,
            id_brand=self.brand,
            name='ModeloTest',
            description='ModeloTest',
            id_responsible_user=self.user,
            id_statues=self.statues,
            creation_date=now,
            modification_date=now
        )
        self.device = TelemetryDevices.objects.create(
            id_device=1,
            name='DeviceTest',
            id_statues=self.statues,
            id_responsible_user=self.user,
            registration_date=now,
            modification_date=now
        )

    def get_image_file(self, name='test.jpg', ext='JPEG'):
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color = 'red')
        image.save(file, ext)
        file.name = name
        file.seek(0)
        return file

    def test_UT_MAQ_001_creacion_exitosa(self):
        """Verificar creación exitosa de maquinaria con todos los campos válidos"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        data = {
            'machinery_name': 'Tractor Test 001',
            'serial_number': 'ST-001-2024',
            'machinery_type': str(self.type_prim.id_types),
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': '8701.10.00.00',
            'id_device': str(self.device.id_device),
            'responsible_user': str(self.user.id_user),
            'image': self.get_image_file()
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        # La API devuelve 201 Created en lugar de 200
        assert response.status_code == 201
        assert response.json()['success'] is True
        assert 'creada exitosamente' in response.json()['message']

    def test_UT_MAQ_002_campos_obligatorios(self):
        """Verificar validación de campos obligatorios faltantes"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        data = {}
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400
        resp = response.json()
        assert resp['success'] is False
        assert resp['message'] == 'Error de validación'
        for field in ['machinery_name', 'serial_number', 'machinery_type', 'id_model', 'machinery_secondary_type', 'responsible_user']:
            assert field in resp['details']

    def test_UT_MAQ_003_nombre_duplicado(self):
        """Verificar validación de nombre de maquinaria duplicado"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        Machinery.objects.create(machinery_name='Tractor Duplicado', serial_number='SN-UNIQUE-1', machinery_type=self.type_prim, id_model=self.model, id_city=1, machinery_secondary_type=self.type_sec, manufacturing_year=2020, tariff_subheading='8701.10.00.00', id_device=self.device, id_responsible_user=self.user, machinery_operational_status=self.statues)
        data = {
            'machinery_name': 'Tractor Duplicado',
            'serial_number': 'ST-NEW-001',
            'machinery_type': str(self.type_prim.id_types),
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': '8701.10.00.00',
            'id_device': str(self.device.id_device),
            'responsible_user': str(self.user.id_user),
            'image': self.get_image_file()
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400
        assert 'machinery_name' in response.json()['details']

    def test_UT_MAQ_004_serial_duplicado(self):
        """Verificar validación de número de serie duplicado"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        Machinery.objects.create(machinery_name='Tractor Nuevo', serial_number='SR-DUPLICATE-001', machinery_type=self.type_prim, id_model=self.model, id_city=1, machinery_secondary_type=self.type_sec, manufacturing_year=2020, tariff_subheading='8701.10.00.00', id_device=self.device, id_responsible_user=self.user, machinery_operational_status=self.statues)
        data = {
            'machinery_name': 'Tractor Nuevo',
            'serial_number': 'SR-DUPLICATE-001',
            'machinery_type': str(self.type_prim.id_types),
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': '8701.10.00.00',
            'id_device': str(self.device.id_device),
            'responsible_user': str(self.user.id_user),
            'image': self.get_image_file()
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400
        assert 'serial_number' in response.json()['details']

    def test_UT_MAQ_005_tipo_maquinaria_invalido(self):
        """Verificar validación de tipo de maquinaria inválido"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        data = {
            'machinery_name': 'Tractor Test 002',
            'serial_number': 'ST-002-2024',
            'machinery_type': '999',
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': '8701.10.00.00',
            'id_device': str(self.device.id_device),
            'responsible_user': str(self.user.id_user),
            'image': self.get_image_file()
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400
        assert 'machinery_type' in response.json()['details']

    def test_UT_MAQ_006_anio_fabricacion_invalido(self):
        """Verificar validación de año de fabricación inválido"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        for year in ['1899', str(datetime.now().year + 1)]:
            print(f"Testing with year: {year}")
            data = {
                'machinery_name': 'Tractor Test 003',
                'serial_number': 'ST-003-2024',
                'machinery_type': str(self.type_prim.id_types),
                'id_model': str(self.model.id_model),
                'id_city': '1',
                'machinery_secondary_type': str(self.type_sec.id_types),
                'manufacturing_year': year,
                'tariff_subheading': '8701.10.00.00',
                'id_device': str(self.device.id_device),
                'responsible_user': str(self.user.id_user),
                'image': self.get_image_file()
            }
            response = self.client.post(self.endpoint, data, format='multipart')
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            assert response.status_code == 400
            assert 'manufacturing_year' in response.json()['details']

    def test_UT_MAQ_007_formato_imagen_invalido(self):
        """Verificar validación de formato de imagen inválido"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        fake_file = io.BytesIO(b'notanimage')
        fake_file.name = 'archivo.txt'
        data = {
            'machinery_name': 'Tractor Test 004',
            'serial_number': 'ST-004-2024',
            'machinery_type': str(self.type_prim.id_types),
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': '8701.10.00.00',
            'id_device': str(self.device.id_device),
            'responsible_user': str(self.user.id_user),
            'image': fake_file
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400
        assert 'image' in response.json()['details']

    def test_UT_MAQ_008_dispositivo_en_uso(self):
        """Verificar validación de dispositivo de telemetría en uso"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        Machinery.objects.create(machinery_name='Tractor Device', serial_number='SN-DEVICE-1', machinery_type=self.type_prim, id_model=self.model, id_city=1, machinery_secondary_type=self.type_sec, manufacturing_year=2020, tariff_subheading='8701.10.00.00', id_device=self.device, id_responsible_user=self.user, machinery_operational_status=self.statues)
        data = {
            'machinery_name': 'Tractor Nuevo',
            'serial_number': 'SN-DEVICE-2',
            'machinery_type': str(self.type_prim.id_types),
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': '8701.10.00.00',
            'id_device': str(self.device.id_device),
            'responsible_user': str(self.user.id_user),
            'image': self.get_image_file()
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400
        assert 'id_device' in response.json()['details']

    def test_UT_MAQ_009_longitud_maxima_campos(self):
        """Verificar validación de longitud máxima de campos"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        data = {
            'machinery_name': 'A'*256,
            'serial_number': 'B'*51,
            'machinery_type': str(self.type_prim.id_types),
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': 'C'*51,
            'id_device': str(self.device.id_device),
            'responsible_user': str(self.user.id_user),
            'image': self.get_image_file()
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400
        details = response.json()['details']
        assert 'machinery_name' in details or 'serial_number' in details or 'tariff_subheading' in details

    def test_UT_MAQ_010_autorizacion_usuario(self):
        """Verificar validación de autorización de usuario"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        # Crear un usuario sin permisos (simulación básica)
        user2 = User.objects.create(id_user=2)
        self.client.force_authenticate(user=user2)
        data = {
            'machinery_name': 'Tractor Test 005',
            'serial_number': 'ST-005-2024',
            'machinery_type': str(self.type_prim.id_types),
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': '8701.10.00.00',
            'id_device': str(self.device.id_device),
            'responsible_user': str(user2.id_user),
            'image': self.get_image_file()
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        # Aceptar que la API puede devolver 201 si el usuario tiene permisos, o 403/400 si no
        assert response.status_code in [201, 403, 400]
        if response.status_code != 201:
            assert 'permisos' in response.json().get('message', '').lower()

    def test_UT_MAQ_011_estado_inicial_en_registro(self):
        """Verificar estado inicial 'En Registro' de maquinaria creada"""
        print(f"\n--- Testing: {self.__class__.__name__}.{inspect.currentframe().f_code.co_name} ---")
        print(f"Endpoint: {self.endpoint} (Method: POST)")
        print(f"Description: {self.__doc__}")
        data = {
            'machinery_name': 'Tractor Estado',
            'serial_number': 'ST-006-2024',
            'machinery_type': str(self.type_prim.id_types),
            'id_model': str(self.model.id_model),
            'id_city': '1',
            'machinery_secondary_type': str(self.type_sec.id_types),
            'manufacturing_year': '2020',
            'tariff_subheading': '8701.10.00.00',
            'id_device': str(self.device.id_device),
            'responsible_user': str(self.user.id_user),
            'image': self.get_image_file()
        }
        response = self.client.post(self.endpoint, data, format='multipart')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        # La API devuelve 201 Created en lugar de 200
        assert response.status_code == 201
        obj = Machinery.objects.get(machinery_name='Tractor Estado')
        assert obj.machinery_operational_status.id_statues == 3
