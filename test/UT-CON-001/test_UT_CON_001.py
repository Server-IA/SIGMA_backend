"""
UT-CON-001: Pruebas unitarias para endpoint de crear contratos establecidos.
Endpoint: POST /established_contracts/create_established_contract/
Permiso: 174 (established_contract.create)
HU: HU-CON-001 - Registrar Contrato
"""

import json
import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta
from decimal import Decimal
from rest_framework.test import APIRequestFactory
from rest_framework import status
from rest_framework.request import Request

import payroll.api.established_contract_viewset as ecv


def make_request(payload_dict, request_data):
    """Helper to build DRF POST Request with auth payload."""
    factory = APIRequestFactory()
    request_obj = factory.post(
        '/established_contracts/create_established_contract/',
        data=request_data,
        format='json'
    )
    
    # Wrap in DRF Request
    request = Request(request_obj)
    
    # Set auth payload
    if payload_dict:
        request.auth = payload_dict.get('payload', {})
        request.user = payload_dict.get('user')
    
    return request


# ============================================================================
# TEST 1: Success - Create contract with minimal required fields
# ============================================================================
def test_create_contract_success_minimal_fields(monkeypatch):
    """Test: Success - create contract with only required fields."""
    # Arrange
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}  # Permission 174
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}]
    }

    request = make_request(user_payload, contract_data)

    # Act
    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data.get('success') == True
    assert 'contract_code' in response.data


# ============================================================================
# TEST 2: Success - Create contract with deductions and increases
# ============================================================================
def test_create_contract_success_with_deductions_increases(monkeypatch):
    """Test: Success - create contract with deductions and increases."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}],
        'established_deductions': [
            {
                'deduction_type': 29,
                'amount_type': 'fijo',
                'amount_value': 10000,
                'application_deduction_type': 'SalarioBase'
            }
        ],
        'established_increases': [
            {
                'increase_type': 31,
                'amount_type': 'Porcentaje',
                'amount_value': 10,
                'application_increase_type': 'SalarioBase'
            }
        ]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data.get('success') == True


# ============================================================================
# TEST 3: Create contract with quincenal payment frequency
# ============================================================================
def test_create_contract_quincenal_frequency(monkeypatch):
    """Test: Success - create contract with quincenal payment frequency (2 payments required)."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'quincenal',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [
            {'id_day_of_week': None, 'date_payment': 16},
            {'id_day_of_week': None, 'date_payment': 1}
        ]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data.get('success') == True


# ============================================================================
# TEST 4: No permission (403)
# ============================================================================
def test_create_contract_no_permission(monkeypatch):
    """Test: Forbidden - user lacks permission 174."""
    user = SimpleNamespace(id=1, username='basic_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 999}]}]}  # Wrong permission
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "No tiene permisos" in response.data.get('message', '')


# ============================================================================
# TEST 5: Missing required field - id_employee_charge
# ============================================================================
def test_create_contract_missing_employee_charge(monkeypatch):
    """Test: Bad request - missing id_employee_charge."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        # Missing id_employee_charge
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get('success') == False
    assert 'id_employee_charge' in response.data.get('errors', {})


# ============================================================================
# TEST 6: Invalid dates - end_date before start_date
# ============================================================================
def test_create_contract_invalid_date_range(monkeypatch):
    """Test: Bad request - end_date before start_date."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(yesterday),  # Before start_date
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get('success') == False
    assert 'end_date' in response.data.get('errors', {})


# ============================================================================
# TEST 7: Negative salary_base
# ============================================================================
def test_create_contract_negative_salary(monkeypatch):
    """Test: Bad request - negative salary_base."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': -100000,  # Negative
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get('success') == False
    assert 'salary_base' in response.data.get('errors', {})


# ============================================================================
# TEST 8: Invalid vacation_days - zero
# ============================================================================
def test_create_contract_zero_vacation_days(monkeypatch):
    """Test: Bad request - vacation_days is zero."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 0,  # Invalid
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get('success') == False
    assert 'vacation_days' in response.data.get('errors', {})


# ============================================================================
# TEST 9: cumulative_vacation=True but missing start_cumulative_vacation
# ============================================================================
def test_create_contract_cumulative_missing_start_date(monkeypatch):
    """Test: Bad request - cumulative_vacation is True but start_cumulative_vacation missing."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': True,  # But no start_cumulative_vacation
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get('success') == False
    assert 'start_cumulative_vacation' in response.data.get('errors', {})


# ============================================================================
# TEST 10: Invalid deduction - amount_value > 100 for Porcentaje type
# ============================================================================
def test_create_contract_invalid_deduction_percentage(monkeypatch):
    """Test: Bad request - deduction amount_value exceeds 100 for percentage type."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}],
        'established_deductions': [
            {
                'deduction_type': 29,
                'amount_type': 'Porcentaje',
                'amount_value': 150,  # > 100 for percentage
                'application_deduction_type': 'SalarioBase'
            }
        ]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get('success') == False


# ============================================================================
# TEST 11: Weekly payment - missing day_of_week
# ============================================================================
def test_create_contract_weekly_missing_day(monkeypatch):
    """Test: Bad request - weekly frequency but day_of_week not specified."""
    user = SimpleNamespace(id=1, username='hr_user', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 174}]}]}
    user_payload = {'user': user, 'payload': payload}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'semanal',  # Weekly
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [
            {'id_day_of_week': None, 'date_payment': None}  # Missing day_of_week
        ]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data.get('success') == False
    assert 'contract_payments' in response.data.get('errors', {})


# ============================================================================
# TEST 12: Unauthenticated user
# ============================================================================
def test_create_contract_unauthenticated(monkeypatch):
    """Test: Unauthorized - user not authenticated."""
    user = SimpleNamespace(id=1, username='anonymous', is_authenticated=False)
    user_payload = {'user': user, 'payload': {}}

    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    contract_data = {
        'id_employee_charge': 1,
        'contract_type': 19,
        'start_date': str(today),
        'end_date': str(tomorrow),
        'payment_frequency_type': 'diario',
        'salary_type': 'Mensual fijo',
        'salary_base': 100000,
        'currency_type': 17,
        'vacation_days': 15,
        'cumulative_vacation': False,
        'maximum_disability_days': 15,
        'overtime': 30,
        'notice_period_days': 10,
        'contract_payments': [{'id_day_of_week': None, 'date_payment': None}]
    }

    request = make_request(user_payload, contract_data)

    viewset = ecv.EstablishedContractViewSet()
    response = viewset.create_established_contract(request)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "no autenticado" in response.data.get('message', '').lower()
