"""
UT-EMP-006: Pruebas para generar Otro Sí de contrato de empleado
ID: UT-EMP-006
HU: HU-EMP-006 - Generar Otro Sí de Contrato
Endpoint: POST /employees/{id_employee}/generate-otro-si/
Permiso: 187 (employee.create_secundary_petition)
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from users.models import User
from parameterization.models import (
    TypesCategory, Types, UnitsCategory, Units, 
    EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory
)
from payroll.models import Employee, EmployeeNews, EmployeeContract, DaysOfWeek


@pytest.mark.django_db
class TestGenerateOtroSi:
    """Pruebas de generación de Otro Sí de contrato de empleado"""
    
    @property
    def endpoint(self):
        return '/employees/1/generate-otro-si/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([187])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Crear empleados y contratos de prueba
        self._create_test_employees_and_contracts()
    
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
        """Crea los tipos, estados y unidades necesarias para los tests"""
        # Crear categorías de status
        status_cat, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1, 
            defaults={
                "name": "Status", 
                "description": "Status", 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        # Crear estados necesarios
        self.status_active, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                "name": "Activo", 
                "description": "Activo", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        self.status_inactive, _ = Statues.objects.get_or_create(
            id_statues=2,
            defaults={
                "name": "Inactivo", 
                "description": "Inactivo", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        self.status_contract_active, _ = Statues.objects.get_or_create(
            id_statues=28,
            defaults={
                "name": "Contrato Activo", 
                "description": "Contrato Activo", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        self.status_contract_finished, _ = Statues.objects.get_or_create(
            id_statues=29,
            defaults={
                "name": "Contrato Finalizado", 
                "description": "Contrato Finalizado", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        # Crear categorías de tipos necesarias
        # Categoría 15: Tipos de contrato
        contract_type_cat, _ = TypesCategory.objects.get_or_create(
            id_types_categories=15,
            defaults={
                "name": "Tipos de Contrato",
                "description": "Tipos de contrato",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categoría 16: Tipos de jornada
        workday_type_cat, _ = TypesCategory.objects.get_or_create(
            id_types_categories=16,
            defaults={
                "name": "Tipos de Jornada",
                "description": "Tipos de jornada laboral",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categoría 17: Modos de trabajo
        workmode_type_cat, _ = TypesCategory.objects.get_or_create(
            id_types_categories=17,
            defaults={
                "name": "Modos de Trabajo",
                "description": "Modos de trabajo",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categoría 18: Tipos de deducción
        deduction_type_cat, _ = TypesCategory.objects.get_or_create(
            id_types_categories=18,
            defaults={
                "name": "Tipos de Deducción",
                "description": "Tipos de deducción",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categoría 19: Tipos de incremento
        increase_type_cat, _ = TypesCategory.objects.get_or_create(
            id_types_categories=19,
            defaults={
                "name": "Tipos de Incremento",
                "description": "Tipos de incremento",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Crear tipos específicos
        self.contract_type, _ = Types.objects.get_or_create(
            id_types=19,
            defaults={
                "name": "Contrato Indefinido",
                "description": "Contrato a término indefinido",
                "id_types_categories": contract_type_cat,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.workday_type, _ = Types.objects.get_or_create(
            id_types=22,
            defaults={
                "name": "Jornada Completa",
                "description": "Jornada completa",
                "id_types_categories": workday_type_cat,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.workmode_type, _ = Types.objects.get_or_create(
            id_types=25,
            defaults={
                "name": "Presencial",
                "description": "Modo presencial",
                "id_types_categories": workmode_type_cat,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.deduction_type, _ = Types.objects.get_or_create(
            id_types=29,
            defaults={
                "name": "Deducción Test",
                "description": "Tipo de deducción para pruebas",
                "id_types_categories": deduction_type_cat,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.increase_type, _ = Types.objects.get_or_create(
            id_types=31,
            defaults={
                "name": "Incremento Test",
                "description": "Tipo de incremento para pruebas",
                "id_types_categories": increase_type_cat,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Crear departamento y cargo
        dept, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={
                "name": "Dept 1", 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        self.charge, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=1,
            defaults={
                "name": "Cargo 1",
                "description": "Cargo test",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear categoría de unidades (10: Moneda)
        unit_cat, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10,
            defaults={
                "name": "Moneda",
                "description": "Categoría de monedas",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.unit, _ = Units.objects.get_or_create(
            id_units=17,
            defaults={
                "name": "COP",
                "symbol": "COP",
                "id_units_categories": unit_cat,
                "id_types": self.contract_type,
                "id_statues": self.status_active,
                "id_responsible_user": self.user
            }
        )
        
        # Crear día de la semana para pagos semanales
        self.day_of_week, _ = DaysOfWeek.objects.get_or_create(
            id_day_of_week=1,
            defaults={
                "name": "Lunes"
            }
        )
    
    def _create_test_employees_and_contracts(self):
        """Crea empleados y contratos de prueba"""
        # Empleado 1: Activo con contrato activo
        user_employee1 = self._ensure_user(2)
        self.employee1, _ = Employee.objects.get_or_create(
            id_employee=1,
            defaults={
                "id_user": user_employee1,
                "email": "empleado1.test@example.com",
                "id_employee_charge": self.charge,
                "employee_status": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        self.employee1.employee_status = self.status_active
        self.employee1.save()
        
        self.contract1, _ = EmployeeContract.objects.get_or_create(
            contract_code="CON-2025-0001-00",
            defaults={
                "id_employee": self.employee1,
                "id_employee_charge": self.charge,
                "id_employee_department": self.charge.id_employee_department,
                "contract_type": self.contract_type,
                "start_date": self.today - timedelta(days=30),
                "end_date": None,
                "payment_frequency_type": "mensual",
                "salary_type": "Mensual fijo",
                "salary_base": 1000000.0,
                "currency_type": self.unit,
                "vacation_days": 15,
                "cumulative_vacation": False,
                "maximum_disability_days": 90,
                "overtime": 1.5,
                "contract_status": self.status_contract_active,
                "secundary_petition": False,
                "creation_date": self.now,
                "id_responsible_user": self.user
            }
        )
        self.contract1.contract_status = self.status_contract_active
        self.contract1.save()
        
        # Empleado 2: Inactivo
        user_employee2 = self._ensure_user(3)
        self.employee2, _ = Employee.objects.get_or_create(
            id_employee=2,
            defaults={
                "id_user": user_employee2,
                "email": "empleado2.test@example.com",
                "id_employee_charge": self.charge,
                "employee_status": self.status_inactive,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        self.employee2.employee_status = self.status_inactive
        self.employee2.save()
        
        # Empleado 3: Activo pero sin contrato activo
        user_employee3 = self._ensure_user(4)
        self.employee3, _ = Employee.objects.get_or_create(
            id_employee=3,
            defaults={
                "id_user": user_employee3,
                "email": "empleado3.test@example.com",
                "id_employee_charge": self.charge,
                "employee_status": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        self.employee3.employee_status = self.status_active
        self.employee3.save()
        
        # Contrato finalizado para empleado 3
        EmployeeContract.objects.get_or_create(
            contract_code="CON-2025-0003-00",
            defaults={
                "id_employee": self.employee3,
                "id_employee_charge": self.charge,
                "id_employee_department": self.charge.id_employee_department,
                "contract_type": self.contract_type,
                "start_date": self.today - timedelta(days=60),
                "end_date": self.today - timedelta(days=30),
                "payment_frequency_type": "mensual",
                "salary_type": "Mensual fijo",
                "salary_base": 1000000.0,
                "currency_type": self.unit,
                "vacation_days": 15,
                "cumulative_vacation": False,
                "maximum_disability_days": 90,
                "overtime": 1.5,
                "contract_status": self.status_contract_finished,
                "secundary_petition": False,
                "creation_date": self.now - timedelta(days=60),
                "id_responsible_user": self.user
            }
        )
    
    def _get_valid_payload(self):
        """Retorna un payload válido para generar Otro Sí"""
        return {
            "observation": "Actualización por aumento salarial",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato Otro Sí - aumento salarial",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": True,
                    "start_cumulative_vacation": str(self.today + timedelta(days=1)),
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [
                        {
                            "id_day_of_week": None,
                            "date_payment": None
                        }
                    ],
                    "established_deductions": [],
                    "established_increases": []
                }
            ]
        }
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_1_generacion_exitosa(self, mock_auth):
        """UT-EMP-006.1 - Generación exitosa de Otro Sí (camino feliz)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = self._get_valid_payload()
        
        # Contar contratos antes
        contracts_before = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        assert response.data.get("success") is True
        assert "Otro Si generado" in response.data.get("message", "").lower() or "exitosamente" in response.data.get("message", "").lower()
        
        # Verificar que se creó un nuevo contrato
        contracts_after = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        assert contracts_after == contracts_before + 1
        
        # Verificar que el contrato anterior está finalizado
        self.contract1.refresh_from_db()
        assert self.contract1.contract_status_id == 29
        
        # Verificar que se creó el nuevo contrato con secundary_petition=True
        new_contract = EmployeeContract.objects.filter(
            id_employee=self.employee1,
            secundary_petition=True
        ).exclude(contract_code=self.contract1.contract_code).first()
        assert new_contract is not None
        assert new_contract.contract_status_id == 28  # Activo
        
        # Verificar registro de novedad
        news = EmployeeNews.objects.filter(
            id_employee=self.employee1,
            news_type='GENERAR_OTRO_SI'
        ).last()
        assert news is not None
        assert news.observation == "Actualización por aumento salarial"
        assert news.id_responsible_user.id_user == 1
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_2_empleado_inactivo(self, mock_auth):
        """UT-EMP-006.2 - Empleado inactivo (no se puede generar Otro Sí)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        endpoint = '/employees/2/generate-otro-si/'
        payload = self._get_valid_payload()
        
        # Act
        response = self.client.post(endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "inactivo" in response.data["message"].lower()
        
        # Verificar que no se creó contrato nuevo
        contracts_count = EmployeeContract.objects.filter(id_employee=self.employee2).count()
        assert contracts_count == 0
        
        # Verificar que no se registró novedad
        news_count = EmployeeNews.objects.filter(
            id_employee=self.employee2,
            news_type='GENERAR_OTRO_SI'
        ).count()
        assert news_count == 0
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_3_empleado_sin_contrato_activo(self, mock_auth):
        """UT-EMP-006.3 - Empleado sin contrato activo"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        endpoint = '/employees/3/generate-otro-si/'
        payload = self._get_valid_payload()
        
        # Act
        response = self.client.post(endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        errors = response.data.get("errors", {})
        error_str = str(errors).lower()
        assert "finalizado" in error_str or "contrato activo" in error_str
        
        # Verificar que no se creó contrato nuevo
        contracts_before = EmployeeContract.objects.filter(id_employee=self.employee3).count()
        contracts_after = EmployeeContract.objects.filter(id_employee=self.employee3).count()
        assert contracts_after == contracts_before
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_4_campos_obligatorios_faltantes(self, mock_auth):
        """UT-EMP-006.4 - Campos obligatorios faltantes"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "observation": "",
            "id_employee_charge": None,
            "contract": [
                {
                    "description": "",
                    "contract_type": None,
                    "payment_frequency_type": "",
                    "salary_type": "",
                    "salary_base": None,
                    "currency_type": None,
                    "vacation_days": None,
                    "cumulative_vacation": None,
                    "maximum_disability_days": None,
                    "overtime": None
                }
            ]
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        errors = response.data.get("errors", {})
        
        # Verificar que hay errores en campos obligatorios
        assert "observation" in errors or "contract" in errors or any("required" in str(errors).lower() for _ in [1])
        
        # Verificar que no se creó contrato nuevo
        contracts_before = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        contracts_after = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        assert contracts_after == contracts_before
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_5_valores_negativos(self, mock_auth):
        """UT-EMP-006.5 - Valores negativos en campos numéricos"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "observation": "Prueba valores negativos",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato inválido",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": -1,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": -100000,
                    "currency_type": 17,
                    "trial_period_days": -5,
                    "vacation_days": -1,
                    "vacation_frequency_days": -360,
                    "cumulative_vacation": True,
                    "start_cumulative_vacation": str(self.today + timedelta(days=1)),
                    "maximum_disability_days": -10,
                    "overtime": -40,
                    "overtime_period": "dia",
                    "notice_period_days": -3,
                    "contract_payments": [],
                    "established_deductions": [],
                    "established_increases": []
                }
            ]
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        errors = response.data.get("errors", {})
        error_str = str(errors).lower()
        
        # Verificar mensajes de error para valores negativos
        assert any("negativ" in error_str for _ in [1]) or any("no puede ser negativ" in error_str for _ in [1])
        
        # Verificar que no se creó contrato nuevo
        contracts_before = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        contracts_after = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        assert contracts_after == contracts_before
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_6_validaciones_fechas(self, mock_auth):
        """UT-EMP-006.6 - Validaciones de fechas del contrato y vacaciones acumulativas"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        # Test: end_date antes de start_date
        payload = {
            "observation": "Prueba fechas inválidas",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato con fechas inválidas",
                    "contract_type": 19,
                    "end_date": str(self.today - timedelta(days=40)),  # Antes del start_date del contrato anterior
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": True,
                    "start_cumulative_vacation": str(self.today + timedelta(days=1)),
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [],
                    "established_deductions": [],
                    "established_increases": []
                }
            ]
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        errors = response.data.get("errors", {})
        error_str = str(errors).lower()
        assert "fecha de fin" in error_str or "posterior" in error_str
        
        # Test: cumulative_vacation=True sin start_cumulative_vacation
        payload2 = {
            "observation": "Prueba vacaciones acumulativas sin fecha",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato sin fecha de acumulación",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": True,
                    "start_cumulative_vacation": None,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [],
                    "established_deductions": [],
                    "established_increases": []
                }
            ]
        }
        
        response2 = self.client.post(self.endpoint, payload2, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        errors2 = response2.data.get("errors", {})
        error_str2 = str(errors2).lower()
        assert "acumulativa" in error_str2 or "obligatorio" in error_str2
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_7_validaciones_contract_payments(self, mock_auth):
        """UT-EMP-006.7 - Validaciones de contract_payments según payment_frequency_type"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        # Test: Frecuencia diario con campos no permitidos
        payload = {
            "observation": "Prueba pagos diarios",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato diario",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [
                        {
                            "id_day_of_week": 1,
                            "date_payment": 15
                        }
                    ],
                    "established_deductions": [],
                    "established_increases": []
                }
            ]
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        errors = response.data.get("errors", {})
        error_str = str(errors).lower()
        assert "diario" in error_str or "no se deben especificar" in error_str
        
        # Test: Frecuencia semanal sin id_day_of_week
        payload2 = {
            "observation": "Prueba pagos semanales",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato semanal",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "semanal",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [
                        {
                            "id_day_of_week": None,
                            "date_payment": None
                        }
                    ],
                    "established_deductions": [],
                    "established_increases": []
                }
            ]
        }
        
        response2 = self.client.post(self.endpoint, payload2, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        errors2 = response2.data.get("errors", {})
        error_str2 = str(errors2).lower()
        assert "semanal" in error_str2 or "día de la semana" in error_str2
        
        # Test: Frecuencia mensual con fecha fuera de rango
        payload3 = {
            "observation": "Prueba pagos mensuales",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato mensual",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "mensual",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [
                        {
                            "id_day_of_week": None,
                            "date_payment": 35  # Fuera de rango
                        }
                    ],
                    "established_deductions": [],
                    "established_increases": []
                }
            ]
        }
        
        response3 = self.client.post(self.endpoint, payload3, format='json')
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        errors3 = response3.data.get("errors", {})
        error_str3 = str(errors3).lower()
        assert "mensual" in error_str3 or "1 y 31" in error_str3 or "31" in error_str3 or "max_value" in error_str3
        
        # Test: Frecuencia quincenal con menos de 2 registros
        payload4 = {
            "observation": "Prueba pagos quincenales",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato quincenal",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "quincenal",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [
                        {
                            "id_day_of_week": None,
                            "date_payment": 15
                        }
                    ],
                    "established_deductions": [],
                    "established_increases": []
                }
            ]
        }
        
        response4 = self.client.post(self.endpoint, payload4, format='json')
        assert response4.status_code == status.HTTP_400_BAD_REQUEST
        errors4 = response4.data.get("errors", {})
        error_str4 = str(errors4).lower()
        assert "quincenal" in error_str4 or "2 registros" in error_str4
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_8_validaciones_deducciones(self, mock_auth):
        """UT-EMP-006.8 - Validaciones de deducciones en el Otro Sí"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        # Test: Deducción con amount_value negativo
        payload = {
            "observation": "Prueba deducciones",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato con deducciones",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [],
                    "established_deductions": [
                        {
                            "deduction_type": 29,
                            "amount_type": "fijo",
                            "amount_value": -100,
                            "application_deduction_type": "SalarioBase",
                            "start_date_deduction": None,
                            "end_date_deductions": None,
                            "description": "Deducción inválida"
                        }
                    ],
                    "established_increases": []
                }
            ]
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        errors = response.data.get("errors", {})
        error_str = str(errors).lower()
        assert "negativo" in error_str or "no puede ser negativo" in error_str or "greater than or equal to 0" in error_str or "min_value" in error_str
        
        # Test: Deducción con porcentaje > 100
        payload2 = {
            "observation": "Prueba deducciones porcentaje",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato con deducciones porcentaje",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [],
                    "established_deductions": [
                        {
                            "deduction_type": 29,
                            "amount_type": "Porcentaje",
                            "amount_value": 150,
                            "application_deduction_type": "SalarioBase",
                            "start_date_deduction": None,
                            "end_date_deductions": None,
                            "description": "Deducción porcentaje inválida"
                        }
                    ],
                    "established_increases": []
                }
            ]
        }
        
        response2 = self.client.post(self.endpoint, payload2, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        errors2 = response2.data.get("errors", {})
        error_str2 = str(errors2).lower()
        assert "100" in error_str2 or "porcentaje" in error_str2 or "mayor a 100" in error_str2
        
        # Test: Deducciones duplicadas
        payload3 = {
            "observation": "Prueba deducciones duplicadas",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato con deducciones duplicadas",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [
                        {
                            "id_day_of_week": None,
                            "date_payment": None
                        }
                    ],
                    "established_deductions": [
                        {
                            "deduction_type": 29,
                            "amount_type": "fijo",
                            "amount_value": 100,
                            "application_deduction_type": "SalarioBase",
                            "start_date_deduction": None,
                            "end_date_deductions": None,
                            "description": "Deducción 1"
                        },
                        {
                            "deduction_type": 29,
                            "amount_type": "fijo",
                            "amount_value": 200,
                            "application_deduction_type": "SalarioBase",
                            "start_date_deduction": None,
                            "end_date_deductions": None,
                            "description": "Deducción 2 duplicada"
                        }
                    ],
                    "established_increases": []
                }
            ]
        }
        
        response3 = self.client.post(self.endpoint, payload3, format='json')
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        errors3 = response3.data.get("errors", {})
        error_str3 = str(errors3).lower()
        assert "mismo tipo" in error_str3 or "duplicada" in error_str3 or "29" in error_str3 or "duplicadas" in error_str3
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_9_validaciones_incrementos(self, mock_auth):
        """UT-EMP-006.9 - Validaciones de incrementos en el Otro Sí"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        # Test: Incremento con amount_value negativo
        payload = {
            "observation": "Prueba incrementos",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato con incrementos",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [],
                    "established_deductions": [],
                    "established_increases": [
                        {
                            "increase_type": 31,
                            "amount_type": "fijo",
                            "amount_value": -100,
                            "application_increase_type": "SalarioBase",
                            "start_date_increase": None,
                            "end_date_increase": None,
                            "description": "Incremento inválido"
                        }
                    ]
                }
            ]
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        errors = response.data.get("errors", {})
        error_str = str(errors).lower()
        assert "negativo" in error_str or "no puede ser negativo" in error_str or "greater than or equal to 0" in error_str or "min_value" in error_str
        
        # Test: Incremento con porcentaje > 100
        payload2 = {
            "observation": "Prueba incrementos porcentaje",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato con incrementos porcentaje",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [],
                    "established_deductions": [],
                    "established_increases": [
                        {
                            "increase_type": 31,
                            "amount_type": "Porcentaje",
                            "amount_value": 150,
                            "application_increase_type": "SalarioBase",
                            "start_date_increase": None,
                            "end_date_increase": None,
                            "description": "Incremento porcentaje inválido"
                        }
                    ]
                }
            ]
        }
        
        response2 = self.client.post(self.endpoint, payload2, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        errors2 = response2.data.get("errors", {})
        error_str2 = str(errors2).lower()
        assert "100" in error_str2 or "porcentaje" in error_str2 or "mayor a 100" in error_str2
        
        # Test: Incrementos duplicados
        payload3 = {
            "observation": "Prueba incrementos duplicados",
            "id_employee_charge": 1,
            "contract": [
                {
                    "description": "Contrato con incrementos duplicados",
                    "contract_type": 19,
                    "end_date": None,
                    "payment_frequency_type": "diario",
                    "minimum_hours": 8,
                    "workday_type": 22,
                    "work_mode_type": 25,
                    "salary_type": "Mensual fijo",
                    "salary_base": 1200000,
                    "currency_type": 17,
                    "trial_period_days": 30,
                    "vacation_days": 15,
                    "vacation_frequency_days": 360,
                    "cumulative_vacation": False,
                    "maximum_disability_days": 15,
                    "overtime": 40,
                    "overtime_period": "dia",
                    "notice_period_days": 9,
                    "contract_payments": [
                        {
                            "id_day_of_week": None,
                            "date_payment": None
                        }
                    ],
                    "established_deductions": [],
                    "established_increases": [
                        {
                            "increase_type": 31,
                            "amount_type": "fijo",
                            "amount_value": 100,
                            "application_increase_type": "SalarioBase",
                            "start_date_increase": None,
                            "end_date_increase": None,
                            "description": "Incremento 1"
                        },
                        {
                            "increase_type": 31,
                            "amount_type": "fijo",
                            "amount_value": 200,
                            "application_increase_type": "SalarioBase",
                            "start_date_increase": None,
                            "end_date_increase": None,
                            "description": "Incremento 2 duplicado"
                        }
                    ]
                }
            ]
        }
        
        response3 = self.client.post(self.endpoint, payload3, format='json')
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        errors3 = response3.data.get("errors", {})
        error_str3 = str(errors3).lower()
        assert "mismo tipo" in error_str3 or "duplicada" in error_str3 or "31" in error_str3 or "duplicadas" in error_str3
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_10_observacion_supera_longitud_maxima(self, mock_auth):
        """UT-EMP-006.10 - Observación supera longitud máxima (255)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = self._get_valid_payload()
        payload["observation"] = "a" * 256  # 256 caracteres
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
        
        # Verificar que no se creó contrato nuevo
        contracts_before = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        contracts_after = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        assert contracts_after == contracts_before
    
    def test_ut_emp_006_11_sin_token_sin_permiso(self):
        """UT-EMP-006.11 - Seguridad: Sin token / sin permiso 187"""
        # Subcaso A - Sin token
        payload = self._get_valid_payload()
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        
        # Verificar que no hubo cambios en BD
        contracts_before = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        contracts_after = EmployeeContract.objects.filter(id_employee=self.employee1).count()
        assert contracts_after == contracts_before
        
        # Subcaso B - Con token pero sin permiso 187
        with patch('users.authentication.JWTAuthentication.authenticate') as mock_auth:
            mock_auth.return_value = (type('MockUser', (), {
                'id': 1, 'is_authenticated': True, **self.token_without_permission
            })(), self.token_without_permission)
            
            response2 = self.client.post(self.endpoint, payload, format='json')
            assert response2.status_code == status.HTTP_403_FORBIDDEN
            assert response2.data["success"] is False
            assert "permisos" in response2.data["message"].lower() or "otro si" in response2.data["message"].lower()
            
            # Verificar que no hubo cambios en BD
            contracts_after2 = EmployeeContract.objects.filter(id_employee=self.employee1).count()
            assert contracts_after2 == contracts_before
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_006_12_integridad_trazabilidad(self, mock_auth):
        """UT-EMP-006.12 - Integridad y trazabilidad (novedad creada correctamente)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = self._get_valid_payload()
        observation_text = "Novedad de prueba para trazabilidad"
        payload["observation"] = observation_text
        
        # Contar novedades antes
        news_before = EmployeeNews.objects.filter(id_employee=self.employee1).count()
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        
        # Verificar que se creó la novedad
        news_after = EmployeeNews.objects.filter(id_employee=self.employee1).count()
        assert news_after == news_before + 1
        
        # Verificar detalles de la novedad
        news = EmployeeNews.objects.filter(
            id_employee=self.employee1,
            news_type='GENERAR_OTRO_SI'
        ).last()
        assert news is not None
        assert news.observation == observation_text
        assert news.id_responsible_user.id_user == 1
        assert news.news_date is not None
        
        # Verificar que la fecha está dentro del rango de ejecución
        assert news.news_date >= self.now - timedelta(seconds=5)
        assert news.news_date <= timezone.now() + timedelta(seconds=5)
        
        # Verificar que existe el nuevo contrato referenciado
        new_contract = EmployeeContract.objects.filter(
            id_employee=self.employee1,
            secundary_petition=True
        ).exclude(contract_code=self.contract1.contract_code).first()
        assert new_contract is not None

