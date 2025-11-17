"""
UT-CON-001: Pruebas unitarias para endpoint de crear contratos establecidos.
Endpoint: POST /established_contracts/create_established_contract/
Permiso: 174 (established_contract.create)
HU: HU-CON-001 - Registrar Contrato
"""

import json
from datetime import datetime, timedelta
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class EstablishedContractCreateTests(APITestCase):
    """Test suite for POST /established_contracts/create_established_contract/"""

    def setUp(self):
        """Set up test client and common test data."""
        self.client = APIClient()
        self.url = '/established_contracts/create_established_contract/'
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)

    def _get_auth_headers(self, has_permission=True):
        """Build JWT auth headers with permission 174 if has_permission is True."""
        payload = {
            'user_id': 1,
            'username': 'hr_user',
            'rol': [
                {
                    'id': 10,
                    'nombre': 'Recursos Humanos',
                    'permisos': [{'id': 174, 'nombre': 'established_contract.create'}] if has_permission else []
                }
            ]
        }
        return {'HTTP_AUTHORIZATION': f'Bearer {json.dumps(payload)}'}

    def _get_minimal_contract_data(self):
        """Return minimal valid contract data for diario frequency."""
        return {
            'id_employee_charge': 1,
            'contract_type': 19,
            'start_date': str(self.today),
            'end_date': str(self.tomorrow),
            'payment_frequency_type': 'diario',
            'salary_type': 'Mensual fijo',
            'salary_base': 100000,
            'currency_type': 17,
            'vacation_days': 15,
            'cumulative_vacation': False,
            'maximum_disability_days': 15,
            'overtime': 30,
            'notice_period_days': 10,
            'contract_payments': [
                {'id_day_of_week': None, 'date_payment': None}
            ]
        }

    # ========================================================================
    # TEST 1: Success - Minimal fields, diario frequency
    # ========================================================================
    def test_create_contract_success_minimal_fields(self):
        """Test: Success - create contract with minimal required fields (diario)."""
        data = self._get_minimal_contract_data()
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('success'), True)
        self.assertIn('contract_code', response.data)

    # ========================================================================
    # TEST 2: Success - Quincenal frequency with deductions and increases
    # ========================================================================
    def test_create_contract_quincenal_with_deductions_increases(self):
        """Test: Success - quincenal with 2 payments, deductions, and increases."""
        data = {
            'id_employee_charge': 1,
            'description': 'Contrato de prueba 1',
            'contract_type': 19,
            'start_date': str(self.today),
            'end_date': str(self.today + timedelta(days=7)),
            'payment_frequency_type': 'quincenal',
            'minimum_hours': 8,
            'workday_type': 22,
            'work_mode_type': 25,
            'salary_type': 'Mensual fijo',
            'salary_base': 100000,
            'currency_type': 17,
            'trial_period_days': 30,
            'vacation_days': 15,
            'vacation_frequency_days': 360,
            'cumulative_vacation': True,
            'start_cumulative_vacation': str(self.today),
            'maximum_disability_days': 15,
            'overtime': 30,
            'overtime_period': 'semana',
            'notice_period_days': 10,
            'contract_payments': [
                {'id_day_of_week': None, 'date_payment': 16},
                {'id_day_of_week': None, 'date_payment': 1}
            ],
            'established_deductions': [
                {
                    'deduction_type': 29,
                    'amount_type': 'fijo',
                    'amount_value': 10000,
                    'application_deduction_type': 'SalarioBase',
                    'start_date_deduction': str(self.today),
                    'end_date_deductions': str(self.today + timedelta(days=1)),
                    'description': 'deduccion 1',
                    'amount': 2
                }
            ],
            'established_increases': [
                {
                    'increase_type': 31,
                    'amount_type': 'Porcentaje',
                    'amount_value': 50,
                    'application_increase_type': 'SalarioBase',
                    'start_date_increase': str(self.today),
                    'end_date_increase': str(self.today + timedelta(days=1)),
                    'description': 'aumento 1',
                    'amount': 3
                }
            ]
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('success'), True)

    # ========================================================================
    # TEST 3: Success - Semanal frequency with day_of_week
    # ========================================================================
    def test_create_contract_semanal_frequency(self):
        """Test: Success - semanal frequency with id_day_of_week specified."""
        data = self._get_minimal_contract_data()
        data['payment_frequency_type'] = 'semanal'
        data['contract_payments'] = [
            {'id_day_of_week': 1, 'date_payment': None}
        ]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('success'), True)

    # ========================================================================
    # TEST 4: No permission (403)
    # ========================================================================
    def test_create_contract_no_permission(self):
        """Test: Forbidden - user lacks permission 174."""
        data = self._get_minimal_contract_data()
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=False)
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('No tiene permiso', response.data.get('message', ''))

    # ========================================================================
    # TEST 5: Unauthenticated user (401)
    # ========================================================================
    def test_create_contract_unauthenticated(self):
        """Test: Unauthorized - user not authenticated."""
        data = self._get_minimal_contract_data()
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========================================================================
    # TEST 6: Missing required field - id_employee_charge
    # ========================================================================
    def test_create_contract_missing_employee_charge(self):
        """Test: Bad request - id_employee_charge is required."""
        data = self._get_minimal_contract_data()
        del data['id_employee_charge']
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('id_employee_charge', response.data.get('errors', {}))

    # ========================================================================
    # TEST 7: Invalid date range - end_date before start_date
    # ========================================================================
    def test_create_contract_invalid_date_range(self):
        """Test: Bad request - end_date before start_date."""
        data = self._get_minimal_contract_data()
        data['end_date'] = str(self.today - timedelta(days=1))
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('end_date', response.data.get('errors', {}))

    # ========================================================================
    # TEST 8: Negative salary_base
    # ========================================================================
    def test_create_contract_negative_salary(self):
        """Test: Bad request - salary_base cannot be negative."""
        data = self._get_minimal_contract_data()
        data['salary_base'] = -100000
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('salary_base', response.data.get('errors', {}))

    # ========================================================================
    # TEST 9: Zero vacation_days
    # ========================================================================
    def test_create_contract_zero_vacation_days(self):
        """Test: Bad request - vacation_days cannot be zero or negative."""
        data = self._get_minimal_contract_data()
        data['vacation_days'] = 0
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('vacation_days', response.data.get('errors', {}))

    # ========================================================================
    # TEST 10: cumulative_vacation=true missing start_cumulative_vacation
    # ========================================================================
    def test_create_contract_cumulative_missing_start_date(self):
        """Test: Bad request - start_cumulative_vacation required when cumulative_vacation=true."""
        data = self._get_minimal_contract_data()
        data['cumulative_vacation'] = True
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('start_cumulative_vacation', response.data.get('errors', {}))

    # ========================================================================
    # TEST 11: Invalid deduction percentage > 100
    # ========================================================================
    def test_create_contract_invalid_deduction_percentage(self):
        """Test: Bad request - deduction Porcentaje amount_value cannot exceed 100."""
        data = self._get_minimal_contract_data()
        data['established_deductions'] = [
            {
                'deduction_type': 29,
                'amount_type': 'Porcentaje',
                'amount_value': 150,
                'application_deduction_type': 'SalarioBase'
            }
        ]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('established_deductions', response.data.get('errors', {}))

    # ========================================================================
    # TEST 12: Semanal without day_of_week
    # ========================================================================
    def test_create_contract_semanal_missing_day(self):
        """Test: Bad request - semanal requires id_day_of_week."""
        data = self._get_minimal_contract_data()
        data['payment_frequency_type'] = 'semanal'
        data['contract_payments'] = [
            {'id_day_of_week': None, 'date_payment': None}
        ]
        
        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
            **self._get_auth_headers(has_permission=True)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('contract_payments', response.data.get('errors', {}))
