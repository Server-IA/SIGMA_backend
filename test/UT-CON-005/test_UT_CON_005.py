"""
UT-CON-005: Pruebas para validar la actualización de contratos preestablecidos
ID: UT-CON-005
HU: HU-CON-005 - Actualizar Contrato Preestablecido
Endpoint: PUT /established_contracts/{contract_code}/update_established_contract/
Permiso: 176 (established_contract.update)
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
class TestEstablishedContractUpdate:
    """Pruebas de validación para actualización de contratos preestablecidos"""
    
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
        self.token_with_permission = self._token_with_permissions([176])
        self.token_without_permission = self._token_with_permissions([999])
        self.invalid_token = "invalid_token"
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Crear contrato base para actualizar
        self._setup_base_contract()
    
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
        
        self.deduction_type_1, _ = Types.objects.get_or_create(
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
        
        self.deduction_type_2, _ = Types.objects.get_or_create(
            id_types=30,
            defaults={
                "name": "Pensión", 
                "description": "Deducción de Pensión", 
                "id_types_categories": cat_18, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.increase_type_1, _ = Types.objects.get_or_create(
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
        
        self.increase_type_2, _ = Types.objects.get_or_create(
            id_types=32,
            defaults={
                "name": "Comisión", 
                "description": "Comisión por ventas", 
                "id_types_categories": cat_19, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Tipo inválido para pruebas
        self.invalid_type, _ = Types.objects.get_or_create(
            id_types=99,
            defaults={
                "name": "Tipo Inválido", 
                "description": "Tipo para pruebas de validación", 
                "id_types_categories": cat_15,  # Categoría incorrecta para deducción
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
    
    def _setup_base_contract(self):
        """Crea el contrato base que será actualizado en las pruebas"""
        self.base_contract = EstablishedContract.objects.create(
            contract_code="CON-ENCARGADODEVENTAS-0012",
            id_employee_charge=self.employee_charge,
            description="Contrato base para actualización",
            contract_type=self.contract_type,
            start_date=self.today,
            end_date=self.today + timedelta(days=365),
            payment_frequency_type="mensual",
            minimum_hours=40,
            workday_type=self.workday_type,
            work_mode_type=self.work_mode_type,
            salary_type="Mensual fijo",
            salary_base=2000000.0,
            currency_type=self.currency,
            trial_period_days=30,
            vacation_days=15,
            cumulative_vacation=False,
            start_cumulative_vacation=None,
            vacation_frequency_days=360,
            maximum_disability_days=180,
            overtime=1.25,
            overtime_period="dia",
            notice_period_days=30,
            established_contract_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        # Pago mensual inicial
        ContractPaymentsEstablishedContract.objects.create(
            date_payment=30,
            established_contracts_contract_code=self.base_contract
        )
    
    def _get_valid_quincenal_payload(self):
        """Retorna un payload válido para actualización quincenal"""
        return {
            "contract_type": 19,
            "start_date": str(self.today),
            "end_date": str(self.today + timedelta(days=365)),
            "payment_frequency_type": "quincenal",
            "minimum_hours": 40,
            "workday_type": 22,
            "work_mode_type": 25,
            "salary_type": "Mensual fijo",
            "salary_base": 3000000.0,
            "currency_type": 17,
            "trial_period_days": 60,
            "vacation_days": 20,
            "cumulative_vacation": True,
            "start_cumulative_vacation": str(self.today),
            "vacation_frequency_days": 360,
            "maximum_disability_days": 180,
            "overtime": 1.5,
            "overtime_period": "dia",
            "notice_period_days": 30,
            "contract_payments": [
                {"date_payment": 15, "id_day_of_week": None},
                {"date_payment": 30, "id_day_of_week": None}
            ],
            "established_deductions": [
                {
                    "deduction_type": 29,
                    "amount_type": "Porcentaje",
                    "amount_value": 4.0,
                    "application_deduction_type": "SalarioBase",
                    "start_date_deduction": str(self.today),
                    "end_date_deductions": str(self.today + timedelta(days=365)),
                    "description": "Deducción de salud",
                    "amount": 120000.0
                }
            ],
            "established_increases": [
                {
                    "increase_type": 31,
                    "amount_type": "fijo",
                    "amount_value": 300000.0,
                    "application_increase_type": "SalarioBase",
                    "start_date_increase": str(self.today),
                    "end_date_increase": str(self.today + timedelta(days=365)),
                    "description": "Bonificación por desempeño",
                    "amount": 300000.0
                }
            ]
        }
    
    def _get_valid_diario_payload(self):
        """Retorna un payload válido para actualización diaria"""
        return {
            "contract_type": 19,
            "start_date": str(self.today),
            "end_date": str(self.today + timedelta(days=365)),
            "payment_frequency_type": "diario",
            "minimum_hours": 8,
            "workday_type": 22,
            "work_mode_type": 25,
            "salary_type": "Por horas",
            "salary_base": 15000.0,
            "currency_type": 17,
            "trial_period_days": 15,
            "vacation_days": 15,
            "cumulative_vacation": False,
            "start_cumulative_vacation": None,
            "vacation_frequency_days": 360,
            "maximum_disability_days": 180,
            "overtime": 1.25,
            "overtime_period": "dia",
            "notice_period_days": 15,
            "contract_payments": [
                {"date_payment": None, "id_day_of_week": None}
            ]
        }
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_1_successful_quincenal_update(self, mock_jwt_decode):
        """
        UT-CON-005.1 – 200 OK – Actualización exitosa (pago quincenal, camino feliz)
        
        Verificar que el endpoint PUT actualiza correctamente un contrato existente 
        cuando se envía un JSON válido con payment_frequency_type = "quincenal".
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_quincenal_payload()
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['success'] == True
        assert 'actualizado exitosamente' in data['message'].lower()
        assert 'errors' not in data
        
        # Verificar en BD
        updated_contract = EstablishedContract.objects.get(contract_code="CON-ENCARGADODEVENTAS-0012")
        assert updated_contract.payment_frequency_type == "quincenal"
        assert updated_contract.salary_base == 3000000.0
        assert updated_contract.vacation_days == 20
        assert updated_contract.cumulative_vacation == True
        
        # Verificar pagos quincenales
        payments = ContractPaymentsEstablishedContract.objects.filter(
            established_contracts_contract_code=updated_contract
        )
        assert len(payments) == 2
        payment_dates = [p.date_payment for p in payments]
        assert 15 in payment_dates
        assert 30 in payment_dates
        
        # Verificar deducciones
        deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=updated_contract
        )
        assert len(deductions) == 1
        assert deductions[0].deduction_type_id == 29
        
        # Verificar incrementos
        increases = EstablishedIncrease.objects.filter(
            established_contracts_contract_code=updated_contract
        )
        assert len(increases) == 1
        assert increases[0].increase_type_id == 31
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_2_successful_diario_update(self, mock_jwt_decode):
        """
        UT-CON-005.2 – 200 OK – Actualización exitosa (pago diario)
        
        Verificar que el endpoint acepta correctamente una actualización con 
        payment_frequency_type = "diario".
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_diario_payload()
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['success'] == True
        
        # Verificar en BD
        updated_contract = EstablishedContract.objects.get(contract_code="CON-ENCARGADODEVENTAS-0012")
        assert updated_contract.payment_frequency_type == "diario"
        assert updated_contract.salary_type == "Por horas"
        assert updated_contract.salary_base == 15000.0
        
        # Verificar pago diario
        payments = ContractPaymentsEstablishedContract.objects.filter(
            established_contracts_contract_code=updated_contract
        )
        assert len(payments) == 1
        assert payments[0].date_payment is None
        assert payments[0].id_day_of_week is None
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_3_missing_required_fields(self, mock_jwt_decode):
        """
        UT-CON-005.3 – 400 Bad Request – Campos obligatorios faltantes
        
        Verificar que el endpoint retorna errores cuando faltan campos obligatorios.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Payload incompleto sin campos obligatorios
        incomplete_payload = {
            "description": "Contrato actualizado"
            # Faltan todos los campos obligatorios
        }
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(incomplete_payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] == False
        assert 'errors' in data
        
        errors = data['errors']
        required_fields = [
            'contract_type', 'start_date', 'end_date', 'payment_frequency_type',
            'salary_type', 'salary_base', 'currency_type', 'vacation_days',
            'cumulative_vacation', 'maximum_disability_days', 'overtime'
        ]
        
        for field in required_fields:
            assert field in errors
            assert 'required' in str(errors[field]).lower()
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_4_negative_values_validation(self, mock_jwt_decode):
        """
        UT-CON-005.4 – 400 Bad Request – Validaciones de rango (valores negativos)
        
        Verificar que el endpoint rechaza valores negativos o fuera de rango.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_quincenal_payload()
        # Introducir valores negativos
        payload.update({
            "minimum_hours": -1,
            "salary_base": -1000,
            "vacation_days": -5,
            "overtime": -10,
            "trial_period_days": -30,
            "maximum_disability_days": -180,
            "notice_period_days": -15
        })
        
        # Agregar deducción con valores inválidos
        payload["established_deductions"] = [
            {
                "deduction_type": 29,
                "amount_type": "Porcentaje",
                "amount_value": 150,  # > 100 para porcentaje
                "application_deduction_type": "SalarioBase",
                "amount": -100  # Negativo
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] == False
        errors = data['errors']
        
        # Verificar errores de valores negativos
        negative_fields = ['minimum_hours', 'salary_base', 'vacation_days', 'overtime']
        for field in negative_fields:
            if field in errors:
                assert 'negativ' in str(errors[field]).lower() or 'greater than' in str(errors[field]).lower()
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_5_date_validation(self, mock_jwt_decode):
        """
        UT-CON-005.5 – 400 Bad Request – Validación de fechas de contrato
        
        Verificar coherencia entre start_date, end_date y fecha actual.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_quincenal_payload()
        # Fechas inválidas
        payload.update({
            "start_date": str(self.today - timedelta(days=1)),  # Anterior a hoy
            "end_date": str(self.today)  # Igual a start_date
        })
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] == False
        errors = data['errors']
        
        # Verificar errores de fechas
        assert 'start_date' in errors or 'end_date' in errors
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_6_cumulative_vacation_validation(self, mock_jwt_decode):
        """
        UT-CON-005.6 – 400 Bad Request – Validación de vacaciones acumulativas
        
        Verificar coherencia de campos de vacaciones acumulativas.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_quincenal_payload()
        # Vacaciones acumulativas sin fecha de inicio
        payload.update({
            "cumulative_vacation": True,
            "start_cumulative_vacation": None
        })
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] == False
        errors = data['errors']
        
        # Verificar error de vacaciones acumulativas
        assert 'start_cumulative_vacation' in errors or any(
            'acumulativ' in str(error).lower() for error in errors.values()
        )
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_7_contract_payments_validation(self, mock_jwt_decode):
        """
        UT-CON-005.7 – 400 Bad Request – Validaciones pago diario/semanal/mensual
        
        Verificar reglas de contract_payments para diferentes frecuencias.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Caso 1: Diario con más de 1 registro
        payload = self._get_valid_diario_payload()
        payload["contract_payments"] = [
            {"date_payment": None, "id_day_of_week": None},
            {"date_payment": None, "id_day_of_week": None}  # Registro extra
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] == False
        
        # Caso 2: Semanal sin id_day_of_week
        payload_semanal = self._get_valid_diario_payload()
        payload_semanal.update({
            "payment_frequency_type": "semanal",
            "contract_payments": [
                {"date_payment": None, "id_day_of_week": None}  # Falta día de semana
            ]
        })
        
        response2 = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload_semanal),
            content_type='application/json'
        )
        
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_8_quincenal_payments_validation(self, mock_jwt_decode):
        """
        UT-CON-005.8 – 400 Bad Request – Validaciones pago quincenal
        
        Verificar reglas específicas para payment_frequency_type = "quincenal".
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Caso 1: Solo 1 registro para quincenal
        payload = self._get_valid_quincenal_payload()
        payload["contract_payments"] = [
            {"date_payment": 15, "id_day_of_week": None}  # Solo 1 registro
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Caso 2: Fechas iguales
        payload["contract_payments"] = [
            {"date_payment": 15, "id_day_of_week": None},
            {"date_payment": 15, "id_day_of_week": None}  # Fechas iguales
        ]
        
        response2 = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        
        # Caso 3: Diferencia menor a 15 días
        payload["contract_payments"] = [
            {"date_payment": 10, "id_day_of_week": None},
            {"date_payment": 20, "id_day_of_week": None}  # Diferencia de 10 días
        ]
        
        response3 = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_9_deductions_validation(self, mock_jwt_decode):
        """
        UT-CON-005.9 – 400 Bad Request – Validación de deducciones
        
        Verificar restricciones sobre established_deductions.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_quincenal_payload()
        
        # Caso 1: Dos deducciones con el mismo tipo
        payload["established_deductions"] = [
            {
                "deduction_type": 29,
                "amount_type": "Porcentaje",
                "amount_value": 4.0,
                "application_deduction_type": "SalarioBase",
                "amount": 100000.0
            },
            {
                "deduction_type": 29,  # Mismo tipo
                "amount_type": "fijo",
                "amount_value": 50000.0,
                "application_deduction_type": "SalarioBase",
                "amount": 50000.0
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Caso 2: Tipo de deducción que no existe
        payload["established_deductions"] = [
            {
                "deduction_type": 999,  # No existe
                "amount_type": "Porcentaje",
                "amount_value": 4.0,
                "application_deduction_type": "SalarioBase",
                "amount": 100000.0
            }
        ]
        
        response2 = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_10_increases_validation(self, mock_jwt_decode):
        """
        UT-CON-005.10 – 400 Bad Request – Validación de incrementos
        
        Verificar restricciones sobre established_increases.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_quincenal_payload()
        
        # Caso 1: Dos incrementos con el mismo tipo
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "Porcentaje",
                "amount_value": 10.0,
                "application_increase_type": "SalarioBase",
                "amount": 200000.0
            },
            {
                "increase_type": 31,  # Mismo tipo
                "amount_type": "fijo",
                "amount_value": 100000.0,
                "application_increase_type": "SalarioBase",
                "amount": 100000.0
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Caso 2: Valores negativos
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "fijo",
                "amount_value": -100000.0,  # Negativo
                "application_increase_type": "SalarioBase",
                "amount": -50000.0  # Negativo
            }
        ]
        
        response2 = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_11_parameterized_types_validation(self, mock_jwt_decode):
        """
        UT-CON-005.11 – 400 Bad Request – Validación de tipos parametrizados
        
        Verificar que los tipos asociados pertenezcan a sus categorías correspondientes.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_quincenal_payload()
        
        # Tipos inválidos
        payload.update({
            "contract_type": 999,  # No existe
            "workday_type": 999,   # No existe
            "work_mode_type": 999, # No existe
            "currency_type": 999   # No existe
        })
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] == False
        errors = data['errors']
        
        # Verificar errores de tipos inválidos
        invalid_type_fields = ['contract_type', 'workday_type', 'work_mode_type', 'currency_type']
        for field in invalid_type_fields:
            if field in errors:
                assert 'not exist' in str(errors[field]).lower() or 'válido' in str(errors[field]).lower()
    
    def test_ut_con_005_12_unauthorized_no_token(self):
        """
        UT-CON-005.12 – 401 Unauthorized – Usuario sin autenticación
        
        Verificar que el endpoint rechaza solicitudes sin token.
        """
        # Arrange - No se envía token
        payload = self._get_valid_quincenal_payload()
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        data = response.json()
        assert 'detail' in data or 'message' in data
        error_message = data.get('detail', data.get('message', ''))
        assert 'autenticado' in error_message.lower() or 'authentication' in error_message.lower() or 'credentials' in error_message.lower()
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_12_forbidden_without_permission(self, mock_jwt_decode):
        """
        UT-CON-005.12 – 403 Forbidden – Usuario sin permiso
        
        Verificar que el endpoint rechaza usuarios sin permiso 176.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_without_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token_without_permission')
        
        payload = self._get_valid_quincenal_payload()
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        data = response.json()
        assert 'message' in data
        assert 'permisos' in data['message'].lower()
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_005_12_not_found_contract(self, mock_jwt_decode):
        """
        UT-CON-005.12 – 404 Not Found – Contrato no existe
        
        Verificar que el endpoint responde 404 cuando el contrato no existe.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_valid_quincenal_payload()
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-NOEXISTE-9999/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Verificar que no se modificó ningún contrato
        contract_count = EstablishedContract.objects.count()
        assert contract_count == 1  # Solo el contrato base
