import pytest
import os
import jwt
from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone

@pytest.mark.django_db
class ToleranceThresholdsDetailTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Crear usuario con permiso 165
        from users.models import User
        user, _ = User.objects.update_or_create(id_user=165, defaults={})
        # Crear dependencias de mantenimiento
        from parameterization.models import TypesCategory, Types, StatuesCategory, Statues
        from maintenance.models import Maintenance
        # StatuesCategory
        statues_cat, _ = StatuesCategory.objects.update_or_create(
            id_statues_categories=1,
            defaults={
                'name': 'Default',
                'description': 'Default',
                'modification_date': timezone.now(),
                'creation_date': timezone.now(),
                'id_responsible_user': user
            }
        )
        # Statues
        statues, _ = Statues.objects.update_or_create(
            id_statues=1,
            defaults={
                'name': 'Operativa',
                'description': 'Maquinaria operativa',
                'id_statues_categories': statues_cat,
                'modification_date': timezone.now(),
                'creation_date': timezone.now(),
                'id_responsible_user': user
            }
        )
        # TypesCategory
        types_cat, _ = TypesCategory.objects.update_or_create(
            id_types_categories=1,
            defaults={
                'name': 'Pesada',
                'description': 'Maquinaria pesada',
                'creation_date': timezone.now(),
                'modification_date': timezone.now(),
                'id_responsible_user': user
            }
        )
        # Types
        types, _ = Types.objects.update_or_create(
            id_types=1,
            defaults={
                'name': 'Tractor',
                'description': 'Tractor agrícola',
                'id_types_categories': types_cat,
                'creation_date': timezone.now(),
                'modification_date': timezone.now(),
                'id_responsible_user': user,
                'id_statues': statues
            }
        )
        # Maintenance
        maintenance, _ = Maintenance.objects.update_or_create(
            id_maintenance=1,
            defaults={
                'name': 'cambio de aceite',
                'description': 'Cambio de aceite',
                'maintenance_type': types,
                'maintenance_status': statues,
                'id_responsible_user': user
            }
        )
        # Crear maquinaria
        from machinery.models import Machinery, Parameters, ToleranceThresholds, OBDFaultMachinery, OBD_Faults, EventTypeMachinery, EventTypes
        machinery, _ = Machinery.objects.update_or_create(
            id_machinery=8,
            defaults={
                'machinery_name': 'Tractor 8',
                'machinery_type': types,
                'machinery_brand': 'John Deere',
                'machinery_model': 'JD8000',
                'machinery_year': 2022,
                'machinery_serial_number': 'JD8000-2022',
                'machinery_status': statues,
            }
        )
        # Parámetros y umbrales
        param1, _ = Parameters.objects.update_or_create(
            id=7,
            defaults={
                'parameter_name': 'Temperatura del Motor',
                'avl_id_parameter': 1001,
                'category': 'Parámetros Mecánicos y de Movimiento',
                'unit': '°C',
            }
        )
        param2, _ = Parameters.objects.update_or_create(
            id=12,
            defaults={
                'parameter_name': 'Consumo instantáneo',
                'avl_id_parameter': 1002,
                'category': 'Niveles de Fluidos y Consumo',
                'unit': 'L/h',
            }
        )
        ToleranceThresholds.objects.update_or_create(
            id=37,
            id_machinery=machinery,
            id_parameter=param1,
            defaults={
                'minimum_threshold': -20.5,
                'maximum_threshold': 80.2,
                'id_maintenance': maintenance,
                'alert_enabled': True
            }
        )
        ToleranceThresholds.objects.update_or_create(
            id=38,
            id_machinery=machinery,
            id_parameter=param2,
            defaults={
                'minimum_threshold': 300.0,
                'maximum_threshold': 30000.0,
                'id_maintenance': maintenance,
                'alert_enabled': True
            }
        )
        # OBD Faults
        obd1, _ = OBD_Faults.objects.update_or_create(
            id_obd_fault=1,
            defaults={
                'code': 'P0087',
                'description': 'Presión de combustible baja',
            }
        )
        obd2, _ = OBD_Faults.objects.update_or_create(
            id_obd_fault=3,
            defaults={
                'code': 'P0093',
                'description': 'Fuga de combustible',
            }
        )
        OBDFaultMachinery.objects.update_or_create(
            id=27,
            id_machinery=machinery,
            id_obd_fault=obd1,
            defaults={
                'alert_enabled': True,
                'id_maintenance': None
            }
        )
        OBDFaultMachinery.objects.update_or_create(
            id=28,
            id_machinery=machinery,
            id_obd_fault=obd2,
            defaults={
                'alert_enabled': False,
                'id_maintenance': None
            }
        )
        # Eventos
        event_type, _ = EventTypes.objects.update_or_create(
            id_event_type=1,
            defaults={
                'name': 'Aceleracion',
            }
        )
        EventTypeMachinery.objects.update_or_create(
            id=23,
            id_machinery=machinery,
            id_event_type=event_type,
            defaults={
                'threshold': 25.5,
                'alert_enabled': True,
                'id_maintenance': None
            }
        )

    def _patch_auth(self, permisos):
        secret = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or 'testsecret'
        payload = {
            "id": 165,
            "email": "testuser@example.com",
            "roles": [
                {
                    "permisos": permisos
                }
            ]
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'

    def test_visualizar_umbrales_maquinaria_con_umbral(self):
        self._patch_auth([{"id": 165}])
        response = self.client.get('/tolerance-thresholds/detail/?machinery_id=8')
        assert response.status_code == 200
        data = response.json().get('data', {})
        assert data.get('id_machinery') == 8
        assert 'tolerance_thresholds' in data
        assert 'obd_fault_machinery' in data
        assert 'event_type_machinery' in data
        categorias = set([t.get('parameter_category') for t in data['tolerance_thresholds']])
        assert 'Parámetros Mecánicos y de Movimiento' in categorias
        assert 'Niveles de Fluidos y Consumo' in categorias

    def test_visualizar_umbrales_maquinaria_sin_umbral(self):
        self._patch_auth([{"id": 165}])
        response = self.client.get('/tolerance-thresholds/detail/?machinery_id=999')
        assert response.status_code == 200
        data = response.json().get('data', {})
        assert data.get('id_machinery') == 999
        assert len(data.get('tolerance_thresholds', [])) == 0

    def test_usuario_sin_permiso(self):
        self._patch_auth([])
        response = self.client.get('/tolerance-thresholds/detail/?machinery_id=8')
        assert response.status_code == 403
        assert 'No tiene permisos para consultar esta información' in response.json().get('message', '')

    def test_error_de_red(self):
        # Este test depende de la simulación de error de red en el backend
        pass

    def test_estructura_de_respuesta(self):
        self._patch_auth([{"id": 165}])
        response = self.client.get('/tolerance-thresholds/detail/?machinery_id=8')
        assert response.status_code == 200
        data = response.json().get('data', {})
        for t in data.get('tolerance_thresholds', []):
            assert 'parameter_category' in t
            assert 'alert_enabled' in t
        for f in data.get('obd_fault_machinery', []):
            assert 'fault_code' in f
            assert 'alert_enabled' in f
        for e in data.get('event_type_machinery', []):
            assert 'event_name' in e
            assert 'threshold' in e
            assert 'alert_enabled' in e
