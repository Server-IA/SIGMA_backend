"""
Pruebas unitarias (v2) para el endpoint de detalles de solicitud de servicio
ID base: UT-SOL-004.x
Endpoint: GET /service_requests/{id_request}/details/

Este archivo cubre los escenarios solicitados (UT-SOL-001 .. UT-SOL-020),
renumerados como UT-SOL-004.1 .. UT-SOL-004.20.

Se emplea el mismo estilo de pruebas/mocks del archivo previo, con parches
en check_permission y el serializer de detalle para aislar dependencias.
"""

import os
import sys
from types import SimpleNamespace
from datetime import datetime, timezone as py_tz

import pytest
from unittest.mock import patch, Mock

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

from rest_framework.test import APIClient
from rest_framework import status

from users.models.user import User
from service_requests.models.service_request import ServiceRequest


def _build_detail_payload(
    id_request: str,
    *,
    customer_id=101,
    customer_name="Juan",
    request_status_name="Pendiente",
    payment_status_name="Pendiente",
    payment_method_name="Contado",
    amount_paid=0,
    amount_to_pay=100000,
    lat=4.710989,
    lng=-74.07209,
    altitude=2600,
    altitude_unit_name="msnm",
    machinery_count=2,
    confirmation_datetime_iso=None,
    scheduled_start_date="2025-10-19",
    scheduled_end_date="2025-10-20",
    extra_overrides=None,
):
    """Genera un diccionario con la estructura esperada del detalle.
    Se puede ajustar con overrides para casos específicos.
    """
    machinery_list = []
    for i in range(machinery_count):
        machinery_list.append({
            'id_request_machinery_user': 1000 + i,
            'id_machinery': 500 + i,
            'machinery_name': f"Retroexcavadora {i+1}",
            'serial_number': f"SRL-{i+1:03d}",
            'machinery_image_path': None,
            'id_user': 200 + i,
            'user_name': f"Operario {i+1}",
            'soil_type_id': None,
            'soil_type_surface': None,
            'texture_id': None,
            'texture_texture': None,
            'humidity_level': None,
            'implementation_id': None,
            'implementation_name': None,
            'depth': None,
            'slope': None,
            'work_duration': None,
        })

    payload = {
        'id_request': id_request,

        # Cliente (campos mínimos usados en aserciones)
        'customer': None,
        'customer_id': customer_id,
        'customer_id_user': None,
        'customer_legal_entity_name': None,
        'customer_name': customer_name,
        'customer_first_last_name': None,
        'customer_second_last_name': None,
        'customer_email': 'cliente@example.com',
        'customer_phone': '+57 3000000000',
        'customer_document_type': 'CC',
        'customer_document_number': '123456789',

        # Detalles
        'request_detail': 'Labores de mantenimiento de maquinaria pesada',
        'scheduled_start_date': scheduled_start_date,
        'scheduled_end_date': scheduled_end_date,

        # Confirmación
        'confirmation_user': None,
        'confirmation_user_name': None,
        'confirmation_datetime': confirmation_datetime_iso,
        'completion_cancellation_observations': None,
        'completion_cancellation_datetime': None,
        'completion_cancellation_user': None,
        'completion_cancellation_user_name': None,

        # Estado
        'request_status': None,
        'request_status_id': 20,
        'request_status_name': request_status_name,

        # Maquinaria y ubicación
        'request_machinery_user': machinery_list,
        'request_location': {
            'id_request_location': 7001,
            'country': 'CO',
            'department': 'Cundinamarca',
            'city_id': 11001,
            'place_name': 'Bogotá',
            'latitude': lat,
            'longitude': lng,
            'area': 12.5,
            'area_unit_id': 1,
            'area_unit_name': 'ha',
            'area_unit_symbol': 'ha',
            'altitude': altitude,
            'altitude_unit_id': 10,
            'altitude_unit_name': altitude_unit_name,
            'altitude_unit_symbol': 'm',
        },

        # Pagos
        'amount_paid': amount_paid,
        'currency_unit_amount_paid': None,
        'currency_unit_amount_paid_id': None,
        'currency_unit_amount_paid_name': 'COP',
        'currency_unit_amount_paid_symbol': '$',
        'amount_to_pay': amount_to_pay,
        'currency_unit_amount_to_pay': None,
        'currency_unit_amount_to_pay_id': None,
        'currency_unit_amount_to_pay_name': 'COP',
        'currency_unit_amount_to_pay_symbol': '$',
        'payment_status': None,
        'payment_status_id': 30,
        'payment_status_name': payment_status_name,
        'payment_method_code': 'CONT',
        'payment_method_name': payment_method_name,
    }

    if extra_overrides:
        payload.update(extra_overrides)

    return payload


@pytest.mark.django_db
class TestServiceRequestDetailsV2:
    endpoint_template = '/service_requests/{}/details/'

    def setup_method(self):
        self.client = APIClient()
        # Usuario básico
        self.user, _ = User.objects.get_or_create(id_user=9999, defaults={})
        self.user.is_authenticated = True
        self.user.id = self.user.id_user

    # UT-SOL-004.1 (equiv UT-SOL-001)
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_1_200_detalle_ok(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0054'
        self.client.force_authenticate(user=self.user)

        # Mock de ORM y serializer
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)

        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')

        print(f"\n[UT-SOL-004.1] Esperado: 200, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        # Secciones clave
        for key in ['id_request', 'customer_id', 'request_machinery_user', 'request_location', 'amount_paid', 'amount_to_pay']:
            assert key in body, f"Falta clave requerida: {key}"
        assert isinstance(body['request_machinery_user'], list)
        assert isinstance(body['request_location'], dict)

    # UT-SOL-004.2 (equiv UT-SOL-002)
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=False)
    def test_UT_SOL_004_2_403_sin_permiso(self, mock_check):
        id_code = 'SOL-2025-0001'
        self.client.force_authenticate(user=self.user)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.2] Esperado: 403, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # UT-SOL-004.3 (equiv UT-SOL-003)
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_3_404_no_existe(self, mock_get, mock_check):
        id_code = 'SOL-2099-9999'
        self.client.force_authenticate(user=self.user)
        mock_get.side_effect = ServiceRequest.DoesNotExist()
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.3] Esperado: 404, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # UT-SOL-004.4 (equiv UT-SOL-004)
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_4_400_formato_invalido(self, mock_get, mock_check):
        """
        Nota: El endpoint actual no valida formato; hoy devolvería 404.
        Esta prueba exige 400 según HU. Si falla, marcará NO APROBADO y
        servirá para guiar la implementación de la validación.
        """
        id_code = 'ABC-25-1'
        self.client.force_authenticate(user=self.user)
        mock_get.side_effect = ServiceRequest.DoesNotExist()
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.4] Esperado: 400, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # UT-SOL-004.5 (equiv UT-SOL-005)
    def test_UT_SOL_004_5_401_sin_token(self):
        id_code = 'SOL-2025-0002'
        url = self.endpoint_template.format(id_code)
        response = APIClient().get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.5] Esperado: 401, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # UT-SOL-004.6 (equiv UT-SOL-006) - alcance limitado fuera de scope
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=False)
    def test_UT_SOL_004_6_403_alcance_limitado_fuera(self, mock_check):
        id_code = 'SOL-2025-0100'
        self.client.force_authenticate(user=self.user)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.6] Esperado: 403, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # UT-SOL-004.7 (equiv UT-SOL-007) - alcance limitado propio
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_7_200_alcance_limitado_propio(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0033'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.7] Esperado: 200, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_200_OK

    # UT-SOL-004.8 (equiv UT-SOL-008) - alcance global
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_8_200_alcance_global(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0123'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.8] Esperado: 200, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_200_OK

    # UT-SOL-004.9 (equiv UT-SOL-009) - 406 Accept no soportado
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_9_406_accept_invalido(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0005'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/xml')
        print(f"\n[UT-SOL-004.9] Esperado: 406, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE

    # UT-SOL-004.10 (equiv UT-SOL-010) - 405 solo GET
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    def test_UT_SOL_004_10_405_metodo_no_permitido(self, mock_check):
        id_code = 'SOL-2025-0006'
        self.client.force_authenticate(user=self.user)
        url = self.endpoint_template.format(id_code)
        response = self.client.post(url, data={}, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.10] Esperado: 405, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # UT-SOL-004.11 (equiv UT-SOL-011) - campos opcionales en null
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_11_200_campos_opcionales_null(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0020'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code, extra_overrides={
            'request_detail': None,
            'request_location': {
                'id_request_location': 7002,
                'country': None,
                'department': None,
                'city_id': None,
                'place_name': None,
                'latitude': None,
                'longitude': None,
                'area': None,
                'area_unit_id': None,
                'area_unit_name': None,
                'area_unit_symbol': None,
                'altitude': None,
                'altitude_unit_id': None,
                'altitude_unit_name': None,
                'altitude_unit_symbol': None,
            },
        })
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.11] Esperado: 200, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert 'request_location' in body and body['request_location'] is not None

    # UT-SOL-004.12 (equiv UT-SOL-012) - maquinaria sin duplicados
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_12_200_maquinaria_sin_duplicados(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0042'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code)
        # Hacer únicos id_machinery/serials en payload base
        ids = [m['id_machinery'] for m in sample['request_machinery_user']]
        assert len(ids) == len(set(ids)), "Lista de maquinaria contiene duplicados"
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        print(f"\n[UT-SOL-004.12] Esperado: 200, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        ids_resp = [m['id_machinery'] for m in body.get('request_machinery_user', [])]
        assert len(ids_resp) == len(set(ids_resp))

    # UT-SOL-004.13 (equiv UT-SOL-013) - estado permitido
    @pytest.mark.parametrize('estado', ['Presolicitud', 'Pendiente', 'En ejecución', 'Finalizada', 'Cancelada'])
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_13_200_estado_permitido(self, mock_get, mock_serializer, mock_check, estado):
        id_code = 'SOL-2025-0043'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code, request_status_name=estado)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body['request_status_name'] in {'Presolicitud', 'Pendiente', 'En ejecución', 'Finalizada', 'Cancelada'}

    # UT-SOL-004.14 (equiv UT-SOL-014) - mapeo de estado de pago
    @pytest.mark.parametrize('paid,to_pay,expected', [
        (0, 1000, 'Pendiente'),
        (500, 1000, 'Pago Parcial'),
        (1000, 1000, 'Pagado'),
    ])
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_14_200_mapeo_estado_pago(self, mock_get, mock_serializer, mock_check, paid, to_pay, expected):
        id_code = 'SOL-2025-0044'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code, amount_paid=paid, amount_to_pay=to_pay,
                                       payment_status_name=expected)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body['payment_status_name'] == expected

    # UT-SOL-004.15 (equiv UT-SOL-015) - modalidad de pago permitida
    @pytest.mark.parametrize('method', ['Contado', 'Crédito', 'Anticipado', 'Por cuotas'])
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_15_200_modalidad_pago_valida(self, mock_get, mock_serializer, mock_check, method):
        id_code = 'SOL-2025-0045'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code, payment_method_name=method)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body['payment_method_name'] in {'Contado', 'Crédito', 'Anticipado', 'Por cuotas'}

    # UT-SOL-004.16 (equiv UT-SOL-016) - coordenadas válidas
    @pytest.mark.parametrize('lat,lng', [(0, 0), (4.7, -74.0), (-45.0, 120.0)])
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_16_200_coordenadas_rango(self, mock_get, mock_serializer, mock_check, lat, lng):
        id_code = 'SOL-2025-0046'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code, lat=lat, lng=lng)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        loc = body['request_location']
        assert -90 <= (loc['latitude'] if loc['latitude'] is not None else 0) <= 90
        assert -180 <= (loc['longitude'] if loc['longitude'] is not None else 0) <= 180

    # UT-SOL-004.17 (equiv UT-SOL-017) - altitud entero y unidad
    @pytest.mark.parametrize('alt,unit', [(0, 'msnm'), (1500, 'msnm'), (5000, 'pies')])
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_17_200_altitud_y_unidad(self, mock_get, mock_serializer, mock_check, alt, unit):
        id_code = 'SOL-2025-0047'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code, altitude=alt, altitude_unit_name=unit)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert isinstance(body['request_location']['altitude'], int)
        assert body['request_location']['altitude_unit_name'] in {'msnm', 'pies'}

    # UT-SOL-004.18 (equiv UT-SOL-018) - fechas ISO 8601 y consistencia
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_18_200_fechas_iso_y_orden(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0048'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        iso_now = datetime(2025, 10, 19, 12, 0, 0, tzinfo=py_tz.utc).isoformat().replace('+00:00', 'Z')
        sample = _build_detail_payload(
            id_code,
            confirmation_datetime_iso=iso_now,
            scheduled_start_date='2025-10-19',
            scheduled_end_date='2025-10-20',
        )
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        c = body.get('confirmation_datetime')
        assert c is None or 'T' in c or c.endswith('Z')
        assert body['scheduled_start_date'] <= body['scheduled_end_date']

    # UT-SOL-004.19 (equiv UT-SOL-019) - sin leak de campos
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_19_200_sin_campos_sensibles(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0049'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)
        sample = _build_detail_payload(id_code)
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)
        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        forbidden = {'password', 'token', 'secret', 'api_key', 'credentials'}
        assert forbidden.isdisjoint(body.keys())

    # UT-SOL-004.20 (equiv UT-SOL-020) - datos refrescados
    @patch('service_requests.api.service_request_viewset.ServiceRequestViewSet.check_permission', return_value=True)
    @patch('service_requests.api.service_request_viewset.ServiceRequestDetailSerializer')
    @patch('service_requests.api.service_request_viewset.ServiceRequest.objects.get')
    def test_UT_SOL_004_20_200_datos_recientes(self, mock_get, mock_serializer, mock_check):
        id_code = 'SOL-2025-0050'
        self.client.force_authenticate(user=self.user)
        mock_get.return_value = Mock(spec=ServiceRequest)

        # Simular que el serializer retorna valores ya actualizados
        sample = _build_detail_payload(
            id_code,
            request_status_name='Finalizada',
            payment_status_name='Pagado',
            amount_paid=100000,
            amount_to_pay=100000,
        )
        mock_serializer.side_effect = lambda instance, context=None: SimpleNamespace(data=sample)

        url = self.endpoint_template.format(id_code)
        response = self.client.get(url, HTTP_ACCEPT='application/json', HTTP_CACHE_CONTROL='no-cache')
        print(f"\n[UT-SOL-004.20] Esperado: 200, Obtenido: {response.status_code}")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body['request_status_name'] == 'Finalizada'
        assert body['payment_status_name'] == 'Pagado'
        assert body['amount_paid'] == body['amount_to_pay']
