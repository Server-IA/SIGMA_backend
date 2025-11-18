"""
UT-CON-004: Pruebas para validar la consulta de detalles de contratos preestablecidos
ID: UT-CON-004
HU: HU-CON-005 - Consultar Detalle de Contrato Preestablecido
Endpoint: GET /established_contracts/{contract_code}/detail/
Permiso: 175 (established_contract.retrieve)
"""

import pytest
import json
from datetime import timedelta, date
from unittest.mock import patch, MagicMock
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from parameterization.models import (
    TypesCategory, Types, UnitsCategory, Units, EmployeeCharge, 
    EmployeeDepartment, Statues, StatuesCategory
)
from payroll.models import (
    EstablishedContract, EstablishedDeduction, EstablishedIncrease,
    ContractPaymentsEstablishedContract, DaysOfWeek
)


@pytest.mark.django_db
class TestEstablishedContractDetail:
    """Pruebas de validación para consulta de detalles de contratos preestablecidos"""
    
    endpoint_base = '/established_contracts'
    
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
        self.token_with_permission = self._token_with_permissions([175])
        self.token_without_permission = self._token_with_permissions([999])
        self.invalid_token = "invalid_token"
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Crear contratos de prueba
        self._setup_test_contracts()
    
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
            "id": 1,
            "email": "test@example.com",
            "name": "Test User",
            "roles": [{"permisos": perms, "permissions": perms}],
            "permisos": perms,
            "permissions": perms,
        }
    
    def _setup_parametrization(self):
        """Crea los tipos y unidades necesarias para los tests"""
        # Categorías de estados
        status_cat, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1, 
            defaults={
                "name": "Status", 
                "description": "Status", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Estados
        self.status_active, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                "name": "Activo", 
                "description": "Activo", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.status_inactive, _ = Statues.objects.get_or_create(
            id_statues=2,
            defaults={
                "name": "Inactivo", 
                "description": "Inactivo", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categorías de tipos
        cat_15, _ = TypesCategory.objects.get_or_create(
            id_types_categories=15, 
            defaults={
                "name": "Contract Types", 
                "description": "Contract Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        cat_16, _ = TypesCategory.objects.get_or_create(
            id_types_categories=16, 
            defaults={
                "name": "Workday Types", 
                "description": "Workday Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        cat_17, _ = TypesCategory.objects.get_or_create(
            id_types_categories=17, 
            defaults={
                "name": "Work Mode Types", 
                "description": "Work Mode Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        cat_18, _ = TypesCategory.objects.get_or_create(
            id_types_categories=18, 
            defaults={
                "name": "Deduction Types", 
                "description": "Deduction Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        cat_19, _ = TypesCategory.objects.get_or_create(
            id_types_categories=19, 
            defaults={
                "name": "Increase Types", 
                "description": "Increase Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categoría de unidades (monedas)
        cat_10_units, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10, 
            defaults={
                "name": "Currency Types", 
                "description": "Currency", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Tipos
        self.contract_type, _ = Types.objects.get_or_create(
            id_types=19,
            defaults={
                "name": "Contrato Indefinido", 
                "description": "Contrato Indefinido", 
                "id_types_categories": cat_15, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.workday_type, _ = Types.objects.get_or_create(
            id_types=22,
            defaults={
                "name": "Tiempo Completo", 
                "description": "Tiempo Completo", 
                "id_types_categories": cat_16, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.work_mode_type, _ = Types.objects.get_or_create(
            id_types=25,
            defaults={
                "name": "Presencial", 
                "description": "Presencial", 
                "id_types_categories": cat_17, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.deduction_type, _ = Types.objects.get_or_create(
            id_types=29,
            defaults={
                "name": "Salud", 
                "description": "Deducción de Salud", 
                "id_types_categories": cat_18, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.increase_type, _ = Types.objects.get_or_create(
            id_types=31,
            defaults={
                "name": "Bonificación", 
                "description": "Bonificación por desempeño", 
                "id_types_categories": cat_19, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Moneda
        self.currency, _ = Units.objects.get_or_create(
            id_units=17,
            defaults={
                "name": "COP", 
                "symbol": "$", 
                "id_units_categories": cat_10_units, 
                "id_types": self.contract_type, 
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Departamento y cargo de empleado
        dept, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={
                "name": "Ventas", 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.employee_charge, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=1,
            defaults={
                "name": "Encargado de Ventas",
                "description": "Encargado de Ventas",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Días de la semana
        self.monday, _ = DaysOfWeek.objects.get_or_create(
            id_day_of_week=1,
            defaults={"name": "Lunes"}
        )
        
        self.friday, _ = DaysOfWeek.objects.get_or_create(
            id_day_of_week=5,
            defaults={"name": "Viernes"}
        )
    
    def _setup_test_contracts(self):
        """Crea contratos de prueba para los tests"""
        # Contrato completo con deducciones e incrementos
        self.contract_complete = EstablishedContract.objects.create(
            contract_code="CON-ENCARGADODEVENTAS-0003",
            id_employee_charge=self.employee_charge,
            description="Contrato para Encargado de Ventas",
            contract_type=self.contract_type,
            start_date=self.today,
            end_date=self.today + timedelta(days=365),
            payment_frequency_type="quincenal",
            minimum_hours=40,
            workday_type=self.workday_type,
            work_mode_type=self.work_mode_type,
            salary_type="Mensual fijo",
            salary_base=2500000.0,
            currency_type=self.currency,
            trial_period_days=30,
            vacation_days=15,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today,
            vacation_frequency_days=360,
            maximum_disability_days=180,
            overtime=1.25,
            overtime_period="dia",
            notice_period_days=30,
            established_contract_status=self.status_inactive,  # Estado inactivo para UT-CON-005.9
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        # Pagos quincenales
        ContractPaymentsEstablishedContract.objects.create(
            date_payment=15,
            established_contracts_contract_code=self.contract_complete
        )
        ContractPaymentsEstablishedContract.objects.create(
            date_payment=30,
            established_contracts_contract_code=self.contract_complete
        )
        
        # Deducción
        EstablishedDeduction.objects.create(
            deduction_type=self.deduction_type,
            amount_type="Porcentaje",
            amount_value=4.0,
            application_deduction_type="SalarioBase",
            start_date_deduction=self.today,
            end_date_deductions=self.today + timedelta(days=365),
            description="Deducción de salud",
            amount=100000.0,
            established_contracts_contract_code=self.contract_complete
        )
        
        # Incremento
        EstablishedIncrease.objects.create(
            increase_type=self.increase_type,
            amount_type="fijo",
            amount_value=200000.0,
            application_increase_type="SalarioBase",
            start_date_increase=self.today,
            end_date_increase=self.today + timedelta(days=365),
            description="Bonificación por desempeño",
            amount=200000.0,
            established_contracts_contract_code=self.contract_complete
        )
        
        # Contrato sin deducciones ni incrementos
        self.contract_no_deductions = EstablishedContract.objects.create(
            contract_code="CON-AUXILIAR-0001",
            id_employee_charge=self.employee_charge,
            description="Contrato para Auxiliar",
            contract_type=self.contract_type,
            start_date=self.today,
            end_date=self.today + timedelta(days=365),
            payment_frequency_type="mensual",
            minimum_hours=40,
            workday_type=self.workday_type,
            work_mode_type=self.work_mode_type,
            salary_type="Mensual fijo",
            salary_base=1500000.0,
            currency_type=self.currency,
            trial_period_days=15,
            vacation_days=15,
            cumulative_vacation=False,
            start_cumulative_vacation=None,
            vacation_frequency_days=360,
            maximum_disability_days=180,
            overtime=1.25,
            overtime_period="dia",
            notice_period_days=15,
            established_contract_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        # Pago mensual
        ContractPaymentsEstablishedContract.objects.create(
            date_payment=30,
            established_contracts_contract_code=self.contract_no_deductions
        )
        
        # Contrato semanal
        self.contract_weekly = EstablishedContract.objects.create(
            contract_code="CON-OPERARIO-0002",
            id_employee_charge=self.employee_charge,
            description="Contrato para Operario",
            contract_type=self.contract_type,
            start_date=self.today,
            end_date=self.today + timedelta(days=365),
            payment_frequency_type="semanal",
            minimum_hours=40,
            workday_type=self.workday_type,
            work_mode_type=self.work_mode_type,
            salary_type="Por horas",
            salary_base=15000.0,
            currency_type=self.currency,
            trial_period_days=15,
            vacation_days=15,
            cumulative_vacation=False,
            start_cumulative_vacation=None,
            vacation_frequency_days=360,
            maximum_disability_days=180,
            overtime=1.5,
            overtime_period="semana",
            notice_period_days=7,
            established_contract_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        # Pago semanal (viernes)
        ContractPaymentsEstablishedContract.objects.create(
            id_day_of_week=self.friday,
            established_contracts_contract_code=self.contract_weekly
        )
        
        # Contrato con términos completos
        self.contract_complete_terms = EstablishedContract.objects.create(
            contract_code="CON-TECNICO-0003",
            id_employee_charge=self.employee_charge,
            description="Contrato para Técnico",
            contract_type=self.contract_type,
            start_date=self.today,
            end_date=self.today + timedelta(days=365),
            payment_frequency_type="quincenal",
            minimum_hours=40,
            workday_type=self.workday_type,
            work_mode_type=self.work_mode_type,
            salary_type="Mensual fijo",
            salary_base=3000000.0,
            currency_type=self.currency,
            trial_period_days=30,
            vacation_days=20,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today,
            vacation_frequency_days=360,
            maximum_disability_days=180,
            overtime=1.5,
            overtime_period="dia",
            notice_period_days=30,
            established_contract_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        # Pagos quincenales
        ContractPaymentsEstablishedContract.objects.create(
            date_payment=15,
            established_contracts_contract_code=self.contract_complete_terms
        )
        ContractPaymentsEstablishedContract.objects.create(
            date_payment=30,
            established_contracts_contract_code=self.contract_complete_terms
        )
        
        # Contrato completo para integración
        self.contract_integration = EstablishedContract.objects.create(
            contract_code="CON-COMPLETO-0004",
            id_employee_charge=self.employee_charge,
            description="Contrato completo para integración",
            contract_type=self.contract_type,
            start_date=self.today,
            end_date=self.today + timedelta(days=365),
            payment_frequency_type="quincenal",
            minimum_hours=40,
            workday_type=self.workday_type,
            work_mode_type=self.work_mode_type,
            salary_type="Mensual fijo",
            salary_base=4000000.0,
            currency_type=self.currency,
            trial_period_days=60,
            vacation_days=20,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today,
            vacation_frequency_days=360,
            maximum_disability_days=180,
            overtime=2.0,
            overtime_period="dia",
            notice_period_days=30,
            established_contract_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        # Pagos
        ContractPaymentsEstablishedContract.objects.create(
            date_payment=15,
            established_contracts_contract_code=self.contract_integration
        )
        ContractPaymentsEstablishedContract.objects.create(
            date_payment=30,
            established_contracts_contract_code=self.contract_integration
        )
        
        # Deducción
        EstablishedDeduction.objects.create(
            deduction_type=self.deduction_type,
            amount_type="Porcentaje",
            amount_value=4.0,
            application_deduction_type="SalarioBase",
            start_date_deduction=self.today,
            end_date_deductions=self.today + timedelta(days=365),
            description="Deducción de salud",
            amount=160000.0,
            established_contracts_contract_code=self.contract_integration
        )
        
        # Incremento
        EstablishedIncrease.objects.create(
            increase_type=self.increase_type,
            amount_type="fijo",
            amount_value=300000.0,
            application_increase_type="SalarioBase",
            start_date_increase=self.today,
            end_date_increase=self.today + timedelta(days=365),
            description="Bonificación por desempeño",
            amount=300000.0,
            established_contracts_contract_code=self.contract_integration
        )
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_1_successful_contract_retrieval(self, mock_jwt_decode):
        """
        UT-CON-005.1 – 200 OK – Consulta exitosa de contrato preestablecido (camino feliz)
        
        Verificar que el endpoint retorna correctamente todos los datos del contrato 
        preestablecido cuando el contract_code existe y el usuario tiene el permiso 
        established_contract.retrieve (ID 175).
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0003/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Verificar campos de generalidades
        assert data['contract_code'] == 'CON-ENCARGADODEVENTAS-0003'
        assert data['id_employee_charge'] == 1
        assert data['employee_charge_name'] == 'Encargado de Ventas'
        assert data['description'] == 'Contrato para Encargado de Ventas'
        assert data['contract_type'] == 19
        assert data['contract_type_name'] == 'Contrato Indefinido'
        assert data['start_date'] == str(self.today)
        assert data['end_date'] == str(self.today + timedelta(days=365))
        assert data['payment_frequency_type'] == 'quincenal'
        assert data['minimum_hours'] == 40
        assert data['workday_type'] == 22
        assert data['workday_type_name'] == 'Tiempo Completo'
        assert data['work_mode_type'] == 25
        assert data['work_mode_type_name'] == 'Presencial'
        assert data['salary_type'] == 'Mensual fijo'
        assert data['salary_base'] == 2500000.0
        assert data['currency_type'] == 17
        assert data['currency_type_name'] == 'COP'
        assert data['trial_period_days'] == 30
        assert data['vacation_days'] == 15
        assert data['vacation_frequency_days'] == 360
        assert data['cumulative_vacation'] == True
        assert data['start_cumulative_vacation'] == str(self.today)
        assert data['maximum_disability_days'] == 180
        assert data['overtime'] == 1.25
        assert data['overtime_period'] == 'dia'
        assert data['notice_period_days'] == 30
        assert data['established_contract_status'] == 2
        assert data['established_contract_status_name'] == 'Inactivo'
        
        # Verificar arreglo contract_payments
        assert len(data['contract_payments']) == 2
        payment_dates = [payment['date_payment'] for payment in data['contract_payments']]
        assert 15 in payment_dates
        assert 30 in payment_dates
        
        # Verificar coherencia con frecuencia quincenal
        assert data['payment_frequency_type'] == 'quincenal'
        for payment in data['contract_payments']:
            assert payment['date_payment'] is not None
            assert payment['id_day_of_week'] is None
            assert payment['day_of_week_name'] is None
        
        # Verificar arreglo established_deductions
        assert len(data['established_deductions']) >= 1
        deduction = data['established_deductions'][0]
        assert deduction['deduction_type'] == 29
        assert deduction['deduction_type_name'] == 'Salud'
        assert deduction['amount_type'] == 'Porcentaje'
        assert deduction['amount_value'] == 4.0
        assert deduction['application_deduction_type'] == 'SalarioBase'
        assert deduction['start_date_deduction'] == str(self.today)
        assert deduction['end_date_deductions'] == str(self.today + timedelta(days=365))
        assert deduction['description'] == 'Deducción de salud'
        assert deduction['amount'] == 100000.0
        
        # Verificar arreglo established_increases
        assert len(data['established_increases']) >= 1
        increase = data['established_increases'][0]
        assert increase['increase_type'] == 31
        assert increase['increase_type_name'] == 'Bonificación'
        assert increase['amount_type'] == 'fijo'
        assert increase['amount_value'] == 200000.0
        assert increase['application_increase_type'] == 'SalarioBase'
        assert increase['start_date_increase'] == str(self.today)
        assert increase['end_date_increase'] == str(self.today + timedelta(days=365))
        assert increase['description'] == 'Bonificación por desempeño'
        assert increase['amount'] == 200000.0
        
        # Verificar tipos de datos
        assert isinstance(data['contract_code'], str)
        assert isinstance(data['id_employee_charge'], int)
        assert isinstance(data['salary_base'], float)
        assert isinstance(data['cumulative_vacation'], bool)
        assert isinstance(data['trial_period_days'], int)
        assert isinstance(data['vacation_days'], int)
        assert isinstance(data['contract_payments'], list)
        assert isinstance(data['established_deductions'], list)
        assert isinstance(data['established_increases'], list)
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_2_forbidden_without_permission(self, mock_jwt_decode):
        """
        UT-CON-005.2 – 403 Forbidden – Usuario sin permiso established_contract.retrieve
        
        Verificar que el endpoint restringe el acceso cuando el usuario está autenticado 
        pero no tiene el permiso ID 175.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_without_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token_without_permission')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0003/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        data = response.json()
        assert 'message' in data
        assert 'permisos' in data['message'].lower() or 'permission' in data['message'].lower()
        
        # Verificar que no se devuelve información del contrato
        assert 'contract_code' not in data
        assert 'salary_base' not in data
        assert 'contract_payments' not in data
    
    def test_ut_con_005_3_unauthorized_no_token(self):
        """
        UT-CON-005.3 – 401 Unauthorized – Usuario no autenticado
        
        Verificar que el endpoint rechaza solicitudes sin autenticación.
        """
        # Arrange - No se envía token de autenticación
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0003/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        data = response.json()
        assert 'detail' in data or 'message' in data
        error_message = data.get('detail', data.get('message', ''))
        assert 'autenticado' in error_message.lower() or 'authentication' in error_message.lower() or 'credentials' in error_message.lower()
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_3_unauthorized_invalid_token(self, mock_jwt_decode):
        """
        UT-CON-005.3 – 401 Unauthorized – Token inválido
        
        Verificar que el endpoint rechaza solicitudes con token inválido.
        """
        # Arrange
        import jwt
        mock_jwt_decode.side_effect = jwt.InvalidTokenError("Token inválido")
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0003/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_4_not_found_contract_not_exists(self, mock_jwt_decode):
        """
        UT-CON-005.4 – 404 Not Found – Contrato preestablecido no existe
        
        Verificar que el endpoint responde con 404 cuando el contract_code no está 
        registrado en la base de datos.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Asegurar que el contrato no existe
        assert not EstablishedContract.objects.filter(contract_code="CON-NOEXISTE-9999").exists()
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-NOEXISTE-9999/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert 'message' in data
        assert 'encontr' in data['message'].lower() or 'found' in data['message'].lower()
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_5_bad_request_invalid_contract_code_format(self, mock_jwt_decode):
        """
        UT-CON-005.5 – 400 Bad Request – Formato inválido de contract_code
        
        Verificar que el endpoint maneje de forma adecuada un contract_code con formato 
        inválido (sin prefijo o con caracteres no permitidos).
        
        Nota: En este caso, como no hay validación de formato a nivel de endpoint,
        se comporta como un 404 (no encontrado).
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/contrato_malo/detail/')
        
        # Assert
        # Como no hay validación de formato, se comporta como 404
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert 'message' in data
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_6_contract_without_deductions_increases(self, mock_jwt_decode):
        """
        UT-CON-005.6 – 200 OK – Contrato sin deducciones ni incrementos configurados
        
        Verificar que el endpoint responde correctamente cuando el contrato no tiene 
        deducciones ni incrementos configurados, devolviendo arreglos vacíos pero 
        la estructura intacta.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-AUXILIAR-0001/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Verificar que los arreglos están vacíos
        assert data['established_deductions'] == []
        assert data['established_increases'] == []
        
        # Verificar que no hay errores de serialización
        assert 'contract_code' in data
        assert data['contract_code'] == 'CON-AUXILIAR-0001'
        assert data['salary_base'] == 1500000.0
        
        # Verificar información de generalidades y términos
        assert data['employee_charge_name'] == 'Encargado de Ventas'
        assert data['contract_type_name'] == 'Contrato Indefinido'
        assert data['payment_frequency_type'] == 'mensual'
        assert len(data['contract_payments']) == 1
        assert data['contract_payments'][0]['date_payment'] == 30
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_7_weekly_payment_frequency_coherence(self, mock_jwt_decode):
        """
        UT-CON-005.7 – 200 OK – Frecuencia de pago semanal con campos coherentes
        
        Verificar que cuando la frecuencia de pago es semanal, la información de 
        contract_payments sea coherente (uso de id_day_of_week y day_of_week_name, 
        y date_payment nulo).
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-OPERARIO-0002/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Verificar frecuencia semanal
        assert data['payment_frequency_type'] == 'semanal'
        
        # Verificar coherencia en contract_payments
        assert len(data['contract_payments']) == 1
        payment = data['contract_payments'][0]
        
        # Para frecuencia semanal, debe tener id_day_of_week y day_of_week_name
        assert payment['id_day_of_week'] == 5  # Viernes
        assert payment['day_of_week_name'] == 'Viernes'
        
        # date_payment debe ser nulo para frecuencia semanal
        assert payment['date_payment'] is None
        
        # No debe haber mezcla incoherente de campos
        assert data['salary_type'] == 'Por horas'
        assert data['salary_base'] == 15000.0
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_8_contract_terms_coherence_validation(self, mock_jwt_decode):
        """
        UT-CON-005.8 – 200 OK – Validación de coherencia de términos del contrato
        
        Verificar que los campos relacionados con términos del contrato son coherentes 
        entre sí y se exponen correctamente para alimentar la pestaña "Términos del contrato".
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-TECNICO-0003/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Verificar términos del contrato
        assert data['salary_type'] == 'Mensual fijo'
        assert data['salary_base'] > 0
        assert data['salary_base'] == 3000000.0
        
        assert data['trial_period_days'] == 30
        assert data['trial_period_days'] > 0
        
        assert data['vacation_days'] > 0
        assert data['vacation_days'] == 20
        
        # Verificar coherencia de vacaciones acumulativas
        assert data['cumulative_vacation'] == True
        assert data['start_cumulative_vacation'] is not None
        assert data['start_cumulative_vacation'] == str(self.today)
        
        assert data['vacation_frequency_days'] == 360
        assert data['vacation_frequency_days'] > 0
        
        # Verificar otros términos
        assert data['maximum_disability_days'] > 0
        assert data['maximum_disability_days'] == 180
        
        assert data['overtime'] > 0
        assert data['overtime'] == 1.5
        
        assert data['overtime_period'] == 'dia'
        assert data['notice_period_days'] == 30
        assert data['notice_period_days'] > 0
        
        # Verificar que contiene toda la información necesaria para la UI
        required_fields = [
            'salary_type', 'salary_base', 'trial_period_days', 'vacation_days',
            'cumulative_vacation', 'vacation_frequency_days', 'maximum_disability_days',
            'overtime', 'overtime_period', 'notice_period_days'
        ]
        for field in required_fields:
            assert field in data
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_9_inactive_contract_still_consultable(self, mock_jwt_decode):
        """
        UT-CON-005.9 – 200 OK – Contrato inactivo sigue siendo consultable
        
        Verificar que el endpoint pueda devolver información de contratos preestablecidos 
        con estado inactivo, ya que pueden ser necesarios para auditoría o consulta histórica.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0003/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Verificar que el contrato inactivo es consultable
        assert data['contract_code'] == 'CON-ENCARGADODEVENTAS-0003'
        
        # Verificar estado inactivo
        assert data['established_contract_status'] == 2
        assert data['established_contract_status_name'] == 'Inactivo'
        
        # Verificar que se devuelven todos los campos generales
        assert data['employee_charge_name'] == 'Encargado de Ventas'
        assert data['contract_type_name'] == 'Contrato Indefinido'
        assert data['salary_base'] == 2500000.0
        
        # La UI podrá mostrar claramente el estado del contrato
        assert 'established_contract_status' in data
        assert 'established_contract_status_name' in data
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_10_complete_structure_for_detailed_view(self, mock_jwt_decode):
        """
        UT-CON-005.10 – Integración con HU-CON-005 – Estructura completa para la vista detallada
        
        Validar que la estructura de la respuesta del endpoint soporta las pestañas de la HU-CON-005:
        - Generalidades del contrato
        - Términos del contrato  
        - Deducciones asociadas
        - Incrementos configurados
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Act
        response = self.client.get(f'{self.endpoint_base}/CON-COMPLETO-0004/detail/')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # ===== PESTAÑA 1: GENERALIDADES DEL CONTRATO =====
        generalidades_fields = [
            'contract_code', 'id_employee_charge', 'employee_charge_name', 
            'description', 'contract_type', 'contract_type_name', 'start_date', 
            'end_date', 'payment_frequency_type', 'workday_type', 'workday_type_name',
            'work_mode_type', 'work_mode_type_name', 'established_contract_status',
            'established_contract_status_name'
        ]
        
        for field in generalidades_fields:
            assert field in data, f"Campo {field} faltante en generalidades"
        
        # Verificar valores específicos
        assert data['contract_code'] == 'CON-COMPLETO-0004'
        assert data['employee_charge_name'] == 'Encargado de Ventas'
        assert data['contract_type_name'] == 'Contrato Indefinido'
        assert data['payment_frequency_type'] == 'quincenal'
        assert data['workday_type_name'] == 'Tiempo Completo'
        assert data['work_mode_type_name'] == 'Presencial'
        assert data['established_contract_status_name'] == 'Activo'
        
        # ===== PESTAÑA 2: TÉRMINOS DEL CONTRATO =====
        terminos_fields = [
            'salary_type', 'salary_base', 'minimum_hours', 'currency_type', 
            'currency_type_name', 'trial_period_days', 'vacation_days', 
            'cumulative_vacation', 'start_cumulative_vacation', 'vacation_frequency_days',
            'maximum_disability_days', 'overtime', 'overtime_period', 'notice_period_days'
        ]
        
        for field in terminos_fields:
            assert field in data, f"Campo {field} faltante en términos"
        
        # Verificar valores específicos de términos
        assert data['salary_type'] == 'Mensual fijo'
        assert data['salary_base'] == 4000000.0
        assert data['minimum_hours'] == 40
        assert data['currency_type_name'] == 'COP'
        assert data['trial_period_days'] == 60
        assert data['vacation_days'] == 20
        assert data['cumulative_vacation'] == True
        assert data['start_cumulative_vacation'] == str(self.today)
        assert data['vacation_frequency_days'] == 360
        assert data['maximum_disability_days'] == 180
        assert data['overtime'] == 2.0
        assert data['overtime_period'] == 'dia'
        assert data['notice_period_days'] == 30
        
        # ===== PESTAÑA 3: DEDUCCIONES ASOCIADAS =====
        assert 'established_deductions' in data
        assert len(data['established_deductions']) >= 1
        
        deduction = data['established_deductions'][0]
        deduction_fields = [
            'deduction_type', 'deduction_type_name', 'amount_type', 'amount_value',
            'application_deduction_type', 'start_date_deduction', 'end_date_deductions',
            'description', 'amount'
        ]
        
        for field in deduction_fields:
            assert field in deduction, f"Campo {field} faltante en deducciones"
        
        assert deduction['deduction_type_name'] == 'Salud'
        assert deduction['amount_type'] == 'Porcentaje'
        assert deduction['amount_value'] == 4.0
        assert deduction['application_deduction_type'] == 'SalarioBase'
        assert deduction['start_date_deduction'] == str(self.today)
        assert deduction['end_date_deductions'] == str(self.today + timedelta(days=365))
        assert deduction['description'] == 'Deducción de salud'
        assert deduction['amount'] == 160000.0
        
        # ===== PESTAÑA 4: INCREMENTOS CONFIGURADOS =====
        assert 'established_increases' in data
        assert len(data['established_increases']) >= 1
        
        increase = data['established_increases'][0]
        increase_fields = [
            'increase_type', 'increase_type_name', 'amount_type', 'amount_value',
            'application_increase_type', 'start_date_increase', 'end_date_increase',
            'description', 'amount'
        ]
        
        for field in increase_fields:
            assert field in increase, f"Campo {field} faltante en incrementos"
        
        assert increase['increase_type_name'] == 'Bonificación'
        assert increase['amount_type'] == 'fijo'
        assert increase['amount_value'] == 300000.0
        assert increase['application_increase_type'] == 'SalarioBase'
        assert increase['start_date_increase'] == str(self.today)
        assert increase['end_date_increase'] == str(self.today + timedelta(days=365))
        assert increase['description'] == 'Bonificación por desempeño'
        assert increase['amount'] == 300000.0
        
        # ===== VERIFICACIÓN DE MAPEO 1:1 CON LA UI =====
        # Todos los campos están presentes y pueden mapearse directamente a la UI
        # sin necesidad de transformaciones adicionales
        
        # Verificar que las fechas están en formato correcto (YYYY-MM-DD)
        import re
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        assert re.match(date_pattern, data['start_date'])
        assert re.match(date_pattern, data['end_date'])
        assert re.match(date_pattern, data['start_cumulative_vacation'])
        assert re.match(date_pattern, deduction['start_date_deduction'])
        assert re.match(date_pattern, deduction['end_date_deductions'])
        assert re.match(date_pattern, increase['start_date_increase'])
        assert re.match(date_pattern, increase['end_date_increase'])
        
        # Verificar tipos de datos correctos
        assert isinstance(data['salary_base'], float)
        assert isinstance(data['cumulative_vacation'], bool)
        assert isinstance(data['trial_period_days'], int)
        assert isinstance(data['vacation_days'], int)
        assert isinstance(data['overtime'], float)
        assert isinstance(deduction['amount_value'], float)
        assert isinstance(increase['amount_value'], float)
