import json
import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta
from django.test import RequestFactory
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status
from rest_framework.request import Request

import monitoring.api.data_viewset as dv


class DummyServiceRequest:
    """Mock ServiceRequest object."""
    DoesNotExist = Exception

    class _mgr:
        def __init__(self, obj=None, exc=None):
            self._obj = obj
            self._exc = exc

        def get(self, id_request=None):
            if self._exc:
                raise self._exc
            return self._obj

    objects = _mgr()


def make_request(monkeypatch, user_payload=None, service_request_obj=None, 
                 service_request_exc=None, machinery_data_result=None, query_params=None):
    """Helper to build request and apply common monkeypatches."""
    
    # Patch ServiceRequest.objects.get behavior
    if service_request_exc is not None:
        DummyServiceRequest.objects = DummyServiceRequest._mgr(obj=None, exc=service_request_exc)
    else:
        DummyServiceRequest.objects = DummyServiceRequest._mgr(obj=service_request_obj, exc=None)
    monkeypatch.setattr(dv, 'ServiceRequest', DummyServiceRequest)

    # Patch get_machinery_data function to return mock data
    def mock_get_machinery_data(request_id, request=None, start_date=None, end_date=None, 
                                machinery_id=None, operator_id=None):
        return machinery_data_result or []
    
    monkeypatch.setattr(dv, 'get_machinery_data', mock_get_machinery_data)

    # Patch DataSerializer if needed
    class MockDataSerializer:
        def __init__(self, data, many=False, context=None):
            self.data = data if isinstance(data, list) else [data]
    
    monkeypatch.setattr(dv, 'DataSerializer', MockDataSerializer)

    # Use APIRequestFactory for proper DRF Request object
    factory = APIRequestFactory()
    
    # Build query string from query_params if provided
    query_string = ''
    if query_params:
        parts = []
        for key, value in query_params.items():
            parts.append(f'{key}={value}')
        query_string = '?' + '&'.join(parts)
    
    request_obj = factory.get(f'/data/{service_request_obj.id_request if service_request_obj else "SOL-2025-0072"}/by_request/{query_string}')
    
    # Wrap it in a DRF Request
    request = Request(request_obj)
    
    # Set auth payload
    if user_payload:
        request.auth = user_payload.get('payload', {})
        request.user = user_payload.get('user')
    
    return request


def test_by_request_success_without_filters(monkeypatch):
    """Test: Success - without any filters, permission 172, request exists."""
    # Arrange
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}  # Permiso correcto
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0072'
        customer = SimpleNamespace(name='Cliente ABC', legal_entity_name='ABC SPA')
        scheduled_start_date = datetime(2025, 11, 6, 23, 10, 0)
        scheduled_end_date = datetime(2025, 11, 6, 23, 13, 0)

    machinery_data = [
        {
            'id_machinery': 1,
            'machinery_name': 'Tractor 1',
            'serial_number': 'S-0001',
            'id_user': 1,
            'user_name': 'Juan Andres Veru',
            'id_device': 11,
            'IMEI': '357894561234567',
            'operating_time_hours': 0.05,
            'total_distance_km': 0.005,
            'effective_working_hours': 0.03,
            'parameters': []
        }
    ]

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(), machinery_data_result=machinery_data)
    viewset = dv.DataViewSet()

    # Act
    response = viewset.by_request(request, pk='SOL-2025-0072')

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['machinery_name'] == 'Tractor 1'
    assert response.data[0]['operating_time_hours'] == 0.05


def test_by_request_success_with_date_filters(monkeypatch):
    """Test: Success - with start_date and end_date filters."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0074'
        customer = SimpleNamespace(name='Cliente XYZ', legal_entity_name='XYZ Ltd')
        scheduled_start_date = datetime(2025, 11, 6, 23, 10, 0)
        scheduled_end_date = datetime(2025, 11, 6, 23, 13, 0)

    machinery_data = [
        {
            'id_machinery': 2,
            'machinery_name': 'Tractor 2',
            'parameters': [
                {
                    'parameter_id': 7,
                    'parameter_name': 'Temperatura del Motor',
                    'unit': '°C',
                    'data_points': [
                        {'id': 733, 'data': 90.0, 'registered_at': '2025-11-06T23:10:10Z', 'alert': False}
                    ],
                    'statistics': {'max_value': 115.0, 'min_value': 1.0, 'average': 78.43}
                }
            ]
        }
    ]

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(), machinery_data_result=machinery_data,
                          query_params={'start_date': '2025-11-06T23:10:10', 'end_date': '2025-11-06T23:13:11'})

    viewset = dv.DataViewSet()
    response = viewset.by_request(request, pk='SOL-2025-0074')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


def test_by_request_success_with_machinery_filter(monkeypatch):
    """Test: Success - with machinery_id filter."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0074'
        customer = SimpleNamespace(name='Cliente XYZ')
        scheduled_start_date = datetime(2025, 11, 6)
        scheduled_end_date = datetime(2025, 11, 6)

    machinery_data = [
        {'id_machinery': 1, 'machinery_name': 'Tractor 1', 'parameters': []}
    ]

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(), machinery_data_result=machinery_data,
                          query_params={'machinery_id': '1'})

    viewset = dv.DataViewSet()
    response = viewset.by_request(request, pk='SOL-2025-0074')

    assert response.status_code == status.HTTP_200_OK


def test_by_request_no_permission(monkeypatch):
    """Test: Forbidden - user without permission 172."""
    user = SimpleNamespace(id=2, username='operario', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 999}]}]}  # Different permission
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0075'

    request = make_request(monkeypatch, user_payload=user_payload, service_request_obj=SR())
    viewset = dv.DataViewSet()

    response = viewset.by_request(request, pk='SOL-2025-0075')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "No tiene permiso" in response.data.get('detail', '')


def test_by_request_request_not_found(monkeypatch):
    """Test: Not found - service request does not exist."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0076'

    exc = DummyServiceRequest.DoesNotExist()
    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(), service_request_exc=exc)
    viewset = dv.DataViewSet()

    response = viewset.by_request(request, pk='SOL-2025-9999')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Solicitud no encontrada" in response.data.get('detail', '')


def test_by_request_invalid_machinery_id_format(monkeypatch):
    """Test: Bad request - machinery_id is not an integer."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0077'

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(),
                          query_params={'machinery_id': 'invalid'})

    viewset = dv.DataViewSet()
    response = viewset.by_request(request, pk='SOL-2025-0077')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "machinery_id debe ser un número entero" in response.data.get('detail', '')


def test_by_request_invalid_operator_id_format(monkeypatch):
    """Test: Bad request - operator_id is not an integer."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0078'

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(),
                          query_params={'operator_id': 'not_a_number'})

    viewset = dv.DataViewSet()
    response = viewset.by_request(request, pk='SOL-2025-0078')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "operator_id debe ser un número entero" in response.data.get('detail', '')


def test_by_request_invalid_date_format(monkeypatch):
    """Test: Invalid ISO 8601 date format (silently accepted as backend ignores invalid dates that parse to None)."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0079'
        customer = SimpleNamespace(name='Cliente ABC')
        scheduled_start_date = datetime(2025, 11, 6)
        scheduled_end_date = datetime(2025, 11, 6)

    machinery_data = [
        {'id_machinery': 1, 'machinery_name': 'Tractor 1', 'parameters': []}
    ]

    # Invalid dates parse to None in parse_datetime, so validation is skipped and no error is returned
    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(),
                          machinery_data_result=machinery_data,
                          query_params={'start_date': 'invalid-date', 'end_date': 'also-invalid'})

    viewset = dv.DataViewSet()
    response = viewset.by_request(request, pk='SOL-2025-0079')

    # Backend returns 200 because invalid dates are silently ignored
    assert response.status_code == status.HTTP_200_OK


def test_by_request_end_date_before_start_date(monkeypatch):
    """Test: Bad request - end_date is before start_date."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0080'

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(),
                          query_params={'start_date': '2025-11-06T23:13:00', 'end_date': '2025-11-06T23:10:00'})

    viewset = dv.DataViewSet()
    response = viewset.by_request(request, pk='SOL-2025-0080')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "La fecha de fin no puede ser anterior" in response.data.get('detail', '')


def test_by_request_success_with_all_filters(monkeypatch):
    """Test: Success - with all filters combined (dates, machinery, operator)."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0074'
        customer = SimpleNamespace(name='Cliente XYZ')
        scheduled_start_date = datetime(2025, 11, 6)
        scheduled_end_date = datetime(2025, 11, 6)

    machinery_data = [
        {'id_machinery': 1, 'machinery_name': 'Tractor 1', 'parameters': []}
    ]

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(), machinery_data_result=machinery_data,
                          query_params={
                              'start_date': '2025-11-06T23:10:10',
                              'end_date': '2025-11-06T23:13:11',
                              'machinery_id': '1',
                              'operator_id': '1'
                          })

    viewset = dv.DataViewSet()
    response = viewset.by_request(request, pk='SOL-2025-0074')

    assert response.status_code == status.HTTP_200_OK


def test_by_request_empty_result_set(monkeypatch):
    """Test: Success with empty result set (no machinery data for filters)."""
    user = SimpleNamespace(id=1, username='jefe_maquinaria', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 172}]}]}
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0081'
        customer = SimpleNamespace(name='Cliente ABC')
        scheduled_start_date = datetime(2025, 11, 6)
        scheduled_end_date = datetime(2025, 11, 6)

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(), machinery_data_result=[],
                          query_params={'machinery_id': '9999'})

    viewset = dv.DataViewSet()
    response = viewset.by_request(request, pk='SOL-2025-0081')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0


def test_by_request_permission_in_multiple_roles(monkeypatch):
    """Test: Success - permission exists in one of multiple user roles."""
    user = SimpleNamespace(id=3, username='multi_role_user', is_authenticated=True)
    payload = {
        'rol': [
            {'permisos': [{'id': 100}]},
            {'permisos': [{'id': 172}]},  # Correct permission in second role
            {'permisos': [{'id': 200}]}
        ]
    }
    user_payload = {'user': user, 'payload': payload}

    class SR:
        id_request = 'SOL-2025-0082'
        customer = SimpleNamespace(name='Cliente Test')
        scheduled_start_date = datetime(2025, 11, 6)
        scheduled_end_date = datetime(2025, 11, 6)

    machinery_data = [
        {'id_machinery': 1, 'machinery_name': 'Tractor 1', 'parameters': []}
    ]

    request = make_request(monkeypatch, user_payload=user_payload, 
                          service_request_obj=SR(), machinery_data_result=machinery_data)
    viewset = dv.DataViewSet()

    response = viewset.by_request(request, pk='SOL-2025-0082')

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
