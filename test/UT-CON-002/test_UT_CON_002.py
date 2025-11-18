"""
UT-CON-002: Pruebas para validar deducciones en contratos establecidos
ID: UT-CON-002
HU: HU-CON-002 - Agregar, Modificar y Eliminar Deducciones
Endpoint: POST /established_contracts/create_established_contract/ (con deducciones)
Permiso: 174 (established_contract.create)
"""

import pytest
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from parameterization.models import TypesCategory, Types, UnitsCategory, Units, EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory


@pytest.mark.django_db
class TestEstablishedContractDeductions:
    """Pruebas de validación de deducciones al crear contratos"""
    
    endpoint = '/established_contracts/create_established_contract/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        self.tomorrow = self.today + timedelta(days=1)
        self.week_later = self.today + timedelta(days=7)
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([174])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
    
    def _ensure_user(self, user_id: int) -> User:
        """Crea o recupera un usuario para pruebas"""
        user, created = User.objects.get_or_create(id_user=user_id)
        user.id = user.id_user
        user.is_authenticated = True
        if created:
            user.save()
        return user
    
    def _token_with_permissions(self, permission_ids):
        """Genera payload de token con permisos específicos"""
        perms = [{"id": perm_id} for perm_id in permission_ids]
        return {
            "roles": [{"permisos": perms, "permissions": perms}],
            "permisos": perms,
            "permissions": perms,
        }
    
    def _setup_parametrization(self):
        """Crea los tipos y unidades necesarias para los tests"""
        cat_15, _ = TypesCategory.objects.get_or_create(id_types_categories=15, defaults={"name": "Contract Types", "description": "Contract Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        cat_16, _ = TypesCategory.objects.get_or_create(id_types_categories=16, defaults={"name": "Workday Types", "description": "Workday Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        cat_17, _ = TypesCategory.objects.get_or_create(id_types_categories=17, defaults={"name": "Work Mode Types", "description": "Work Mode Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        cat_18, _ = TypesCategory.objects.get_or_create(id_types_categories=18, defaults={"name": "Deduction Types", "description": "Deduction Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        cat_19, _ = TypesCategory.objects.get_or_create(id_types_categories=19, defaults={"name": "Increase Types", "description": "Increase Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        cat_10_units, _ = UnitsCategory.objects.get_or_create(id_units_categories=10, defaults={"name": "Currency Types", "description": "Currency", "creation_date": timezone.now(), "modification_date": timezone.now()})
        
        status_cat, _ = StatuesCategory.objects.get_or_create(id_statues_categories=1, defaults={"name": "Status", "description": "Status", "creation_date": timezone.now(), "modification_date": timezone.now()})
        status_obj, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={"name": "Active", "description": "Active", "id_statues_categories": status_cat, "creation_date": timezone.now(), "modification_date": timezone.now()}
        )
        
        for type_id, cat in [(19, cat_15), (22, cat_16), (25, cat_17), (29, cat_18), (30, cat_18), (31, cat_19), (32, cat_19)]:
            Types.objects.get_or_create(
                id_types=type_id,
                defaults={"name": f"Type {type_id}", "description": f"Type {type_id}", "id_types_categories": cat, "id_statues": status_obj, "creation_date": timezone.now(), "modification_date": timezone.now()}
            )
        
        Units.objects.get_or_create(
            id_units=17,
            defaults={"name": "COP", "symbol": "$", "id_units_categories": cat_10_units, "id_types": Types.objects.get(id_types=19), "id_statues": status_obj}
        )
        
        dept, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={"name": "Dept 1", "id_statues": status_obj, "creation_date": timezone.now(), "modification_date": timezone.now()}
        )
        
        EmployeeCharge.objects.get_or_create(
            id_employee_charge=1,
            defaults={
                "name": "Cargo 1",
                "description": "Cargo test",
                "id_employee_department": dept,
                "id_statues": status_obj,
                "creation_date": timezone.now(),
                "modification_date": timezone.now()
            }
        )
    
    def _get_base_payload(self):
        """Base para contratos con deducciones"""
        return {
            "id_employee_charge": 1,
            "contract_type": 19,
            "start_date": str(self.today),
            "end_date": str(self.week_later),
            "payment_frequency_type": "quincenal",
            "minimum_hours": 8,
            "workday_type": 22,
            "work_mode_type": 25,
            "salary_type": "Mensual fijo",
            "salary_base": 100000,
            "currency_type": 17,
            "trial_period_days": 30,
            "vacation_days": 15,
            "vacation_frequency_days": 360,
            "cumulative_vacation": True,
            "start_cumulative_vacation": str(self.today),
            "maximum_disability_days": 15,
            "overtime": 30,
            "overtime_period": "semana",
            "notice_period_days": 10,
            "contract_payments": [
                {"id_day_of_week": None, "date_payment": 16},
                {"id_day_of_week": None, "date_payment": 1}
            ],
            "established_deductions": [],
            "established_increases": []
        }
    
    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_1_contrato_con_deduccion_fija_exitosa(self, mock_audit):
        """Crear contrato con deducción fija exitosa retorna 201"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Contrato con deducción fija'
        payload['established_deductions'] = [{
            "deduction_type": 29,
            "amount_type": "fijo",
            "amount_value": 10000,
            "application_deduction_type": "SalarioBase",
            "start_date_deduction": str(self.today),
            "end_date_deductions": str(self.tomorrow),
            "description": "deduccion test",
            "amount": 2
        }]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        if response.status_code != 201:
            errors = response.data.get('errors', response.data)
            error_details = json.dumps(errors, indent=2, default=str)
            raise AssertionError(f"Expected 201 but got {response.status_code}.\nErrors:\n{error_details}")
        
        assert response.data.get('success') is True
        assert 'contract_code' in response.data

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_2_contrato_con_deduccion_porcentaje(self, mock_audit):
        """Crear contrato con deducción porcentaje válido retorna 201"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Contrato con deducción porcentaje'
        payload['established_deductions'] = [{
            "deduction_type": 30,
            "amount_type": "Porcentaje",
            "amount_value": 5.5,
            "application_deduction_type": "SalarioBase",
            "start_date_deduction": str(self.today),
            "end_date_deductions": str(self.tomorrow),
            "description": "deduccion porcentaje",
            "amount": 1
        }]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED, f"Expected 201 but got {response.status_code}. Errors: {response.data}"
        assert response.data.get('success') is True

    def test_ut_con_002_3_sin_autenticacion_retorna_401(self):
        """Sin autenticación retorna 401"""
        payload = self._get_base_payload()
        payload['description'] = 'Test sin auth'
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_4_sin_permiso_retorna_403(self, mock_audit):
        """Sin permiso retorna 403"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_without_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Test sin permiso'
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_5_deduccion_tipo_invalido(self, mock_audit):
        """Tipo de deducción inválido retorna 400"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Deducción tipo inválido'
        payload['established_deductions'] = [{
            "deduction_type": 999,
            "amount_type": "fijo",
            "amount_value": 10000,
            "application_deduction_type": "SalarioBase"
        }]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_6_amount_value_negativo(self, mock_audit):
        """Amount_value negativo retorna 400"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Deducción monto negativo'
        payload['established_deductions'] = [{
            "deduction_type": 29,
            "amount_type": "fijo",
            "amount_value": -5000,
            "application_deduction_type": "SalarioBase",
            "start_date_deduction": str(self.today),
            "end_date_deductions": str(self.tomorrow)
        }]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_7_porcentaje_mayor_100(self, mock_audit):
        """Porcentaje mayor a 100 retorna 400"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Deducción porcentaje > 100'
        payload['established_deductions'] = [{
            "deduction_type": 29,
            "amount_type": "Porcentaje",
            "amount_value": 150,
            "application_deduction_type": "SalarioBase",
            "start_date_deduction": str(self.today),
            "end_date_deductions": str(self.tomorrow)
        }]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_8_fecha_fin_anterior_inicio(self, mock_audit):
        """Fecha de fin anterior a inicio retorna 400"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Deducción fechas inválidas'
        payload['established_deductions'] = [{
            "deduction_type": 29,
            "amount_type": "fijo",
            "amount_value": 10000,
            "application_deduction_type": "SalarioBase",
            "start_date_deduction": str(self.today),
            "end_date_deductions": str(self.today - timedelta(days=1))
        }]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_9_campo_obligatorio_faltante(self, mock_audit):
        """Campo obligatorio faltante en deducción retorna 400"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Deducción campo faltante'
        payload['established_deductions'] = [{
            "amount_type": "fijo",
            "amount_value": 10000,
            "application_deduction_type": "SalarioBase"
        }]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_10_multiples_deducciones_exitosa(self, mock_audit):
        """Crear contrato con múltiples deducciones exitosa retorna 201"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Contrato con múltiples deducciones'
        payload['established_deductions'] = [
            {
                "deduction_type": 29,
                "amount_type": "fijo",
                "amount_value": 10000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today),
                "end_date_deductions": str(self.tomorrow),
                "description": "deduccion 1",
                "amount": 2
            },
            {
                "deduction_type": 30,
                "amount_type": "Porcentaje",
                "amount_value": 3.5,
                "application_deduction_type": "SalarioFinal",
                "start_date_deduction": str(self.today),
                "end_date_deductions": str(self.week_later),
                "description": "deduccion 2",
                "amount": 1
            }
        ]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED, f"Expected 201 but got {response.status_code}. Errors: {response.data}"
        assert response.data.get('success') is True

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_11_deduccion_misma_aplicacion_mismo_tipo(self, mock_audit):
        """Dos deducciones mismo tipo sin justificación retorna 400"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Deducción duplicada'
        payload['established_deductions'] = [
            {
                "deduction_type": 29,
                "amount_type": "fijo",
                "amount_value": 10000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today),
                "end_date_deductions": str(self.tomorrow)
            },
            {
                "deduction_type": 29,
                "amount_type": "fijo",
                "amount_value": 5000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.tomorrow),
                "end_date_deductions": str(self.week_later)
            }
        ]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('payroll.api.established_contract_viewset.AuditClient')
    def test_ut_con_002_12_descripcion_excede_max_caracteres(self, mock_audit):
        """Descripción deducción excede max caracteres (255) retorna 400"""
        mock_audit.return_value.create = MagicMock()
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = self.token_with_permission
        
        payload = self._get_base_payload()
        payload['description'] = 'Deducción descripción larga'
        payload['established_deductions'] = [{
            "deduction_type": 29,
            "amount_type": "fijo",
            "amount_value": 10000,
            "application_deduction_type": "SalarioBase",
            "start_date_deduction": str(self.today),
            "end_date_deductions": str(self.tomorrow),
            "description": "x" * 256,
            "amount": 1
        }]
        
        response = self.client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
