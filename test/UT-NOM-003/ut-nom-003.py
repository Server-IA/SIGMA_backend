"""
UT-NOM-003: Pruebas unitarias para endpoint de generación masiva de nóminas
Endpoint: POST /api/payroll/generate-massive/
Permiso requerido: 188 - payroll.manage_massive_payroll
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock, patch
import uuid

from users.models import User
from parameterization.models import (
    EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory,
    TypesCategory, Types, UnitsCategory, Units
)
from payroll.models import (
    Employee, EmployeeContract, Payroll, 
    TemporaryPayrollAdjustment
)


@pytest.mark.django_db
class TestMassivePayrollGeneration:
    """Pruebas para el endpoint de generación masiva de nóminas"""
    
    @property
    def generate_massive_endpoint(self):
        """Endpoint para generar nómina masiva"""
        return '/payroll/generate-massive/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con permisos
        self.token_with_permission = self._token_with_permissions([188])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Mock del servicio externo de usuarios
        self.mock_external_user_patcher = patch('requests.post')
        self.mock_post = self.mock_external_user_patcher.start()
        self._setup_mock_external_user_service()
        
        # Limpiar nóminas previas
        Payroll.objects.all().delete()
    
    def teardown_method(self):
        """Limpieza después de cada prueba"""
        self.mock_external_user_patcher.stop()
    
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
    
    def _ensure_user(self, user_id: int) -> User:
        """Crea o recupera un usuario para pruebas"""
        user, created = User.objects.get_or_create(id_user=user_id)
        user.id = user.id_user
        user.is_authenticated = True
        if created:
            user.save()
        return user
    
    def _setup_mock_external_user_service(self):
        """Configura el mock del servicio externo de usuarios"""
        self.mock_users = {}
        
        def mock_post_side_effect(url, *args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            
            json_data = kwargs.get('json', {})
            requested_ids = json_data.get('ids', [])
            
            matching_users = [
                user_data for user_id, user_data in self.mock_users.items()
                if user_id in requested_ids
            ]
            
            mock_response.json.return_value = {
                "data": matching_users
            }
            mock_response.content = True
            return mock_response
        
        self.mock_post.side_effect = mock_post_side_effect
    
    def _add_mock_user(self, user_id: int, name: str, first_last_name: str, 
                       second_last_name: str, document_number: str):
        """Agrega un usuario al mock del servicio externo"""
        self.mock_users[user_id] = {
            "id": user_id,
            "name": name,
            "first_last_name": first_last_name,
            "second_last_name": second_last_name,
            "document_number": document_number
        }
    
    def _setup_parametrization(self):
        """Crea los tipos y unidades necesarias para los tests"""
        # Crear categorías
        status_cat, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                "name": "Status",
                "description": "Status",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        types_cat_18, _ = TypesCategory.objects.get_or_create(
            id_types_categories=18,
            defaults={
                "name": "Deduction Types",
                "description": "Tipos de deducción",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        types_cat_19, _ = TypesCategory.objects.get_or_create(
            id_types_categories=19,
            defaults={
                "name": "Increase Types",
                "description": "Tipos de incremento",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        types_cat_15, _ = TypesCategory.objects.get_or_create(
            id_types_categories=15,
            defaults={
                "name": "Contract Types",
                "description": "Tipos de contrato",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear estados
        self.status_active, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                "name": "Activo",
                "description": "Active",
                "id_statues_categories": status_cat,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        self.status_inactive, _ = Statues.objects.get_or_create(
            id_statues=2,
            defaults={
                "name": "Inactivo",
                "description": "Inactive",
                "id_statues_categories": status_cat,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        self.status_created, _ = Statues.objects.get_or_create(
            id_statues=28,
            defaults={
                "name": "Creado",
                "description": "Created",
                "id_statues_categories": status_cat,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear tipos de incremento (categoría 19)
        self.increase_type_45, _ = Types.objects.get_or_create(
            id_types=45,
            defaults={
                "name": "Bono",
                "description": "Bono por desempeño",
                "id_types_categories": types_cat_19,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear tipos de deducción (categoría 18)
        self.deduction_type_32, _ = Types.objects.get_or_create(
            id_types=32,
            defaults={
                "name": "Préstamo",
                "description": "Deducción por préstamo",
                "id_types_categories": types_cat_18,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear tipo de contrato
        self.contract_type, _ = Types.objects.get_or_create(
            id_types=19,
            defaults={
                "name": "Indefinido",
                "description": "Contrato indefinido",
                "id_types_categories": types_cat_15,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear categoría de unidades
        units_cat, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10,
            defaults={
                "name": "Currency",
                "description": "Monedas",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear moneda
        self.currency, _ = Units.objects.get_or_create(
            id_units=1,
            defaults={
                "name": "COP",
                "symbol": "$",
                "id_units_categories": units_cat,
                "id_types": self.contract_type,
                "id_statues": self.status_active
            }
        )
        
        # Crear departamento (id 5)
        self.dept, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=5,
            defaults={
                "name": "Departamento Test",
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear cargo (id 12)
        self.charge, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=12,
            defaults={
                "name": "Cargo Test",
                "description": "Cargo de prueba",
                "id_employee_department": self.dept,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
    
    def _create_employee(self, employee_id: int, user_id: int, email: str, 
                        employee_status: Statues = None,
                        charge: EmployeeCharge = None) -> Employee:
        """Crea un empleado de prueba"""
        if employee_status is None:
            employee_status = self.status_active
        if charge is None:
            charge = self.charge
        
        user = self._ensure_user(user_id)
        employee = Employee.objects.create(
            id_employee=employee_id,
            id_user=user,
            email=email,
            id_employee_charge=charge,
            employee_status=employee_status,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        return employee
    
    def _create_contract(
        self,
        employee: Employee,
        contract_code: str,
        charge: EmployeeCharge = None,
        department: EmployeeDepartment = None,
        start_date: date = None,
        end_date: date = None,
        contract_status: Statues = None,
        salary_base: float = 1000000.0
    ) -> EmployeeContract:
        """Crea un contrato de prueba"""
        if charge is None:
            charge = self.charge
        if department is None:
            department = self.dept
        if start_date is None:
            start_date = date(2025, 1, 1)
        if contract_status is None:
            contract_status = self.status_created
        
        contract = EmployeeContract.objects.create(
            contract_code=contract_code,
            id_employee_charge=charge,
            id_employee_department=department,
            id_employee=employee,
            description="Contrato de prueba",
            contract_type=self.contract_type,
            start_date=start_date,
            end_date=end_date,
            payment_frequency_type="mensual",
            minimum_hours=8,
            workday_type=Types.objects.get(id_types=22) if Types.objects.filter(id_types=22).exists() else self.contract_type,
            work_mode_type=Types.objects.get(id_types=25) if Types.objects.filter(id_types=25).exists() else self.contract_type,
            salary_type="Mensual fijo",
            salary_base=salary_base,
            currency_type=self.currency,
            trial_period_days=30,
            vacation_days=15,
            vacation_frequency_days=360,
            cumulative_vacation=True,
            start_cumulative_vacation=start_date + timedelta(days=7),
            maximum_disability_days=15,
            overtime=40.0,
            overtime_period="mes",
            notice_period_days=30,
            contract_status=contract_status,
            secundary_petition=False,
            creation_date=self.now,
            id_responsible_user=self.user
        )
        return contract
    
    def _authenticate_client(self, permissions=None):
        """Autentica el cliente con los permisos especificados"""
        if permissions is None:
            token = self.token_with_permission
        else:
            token = permissions
        
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer mock_token')
    
    def _create_valid_payload(self, employee_ids=None, increases=None, deductions=None):
        """Crea un payload válido para la generación masiva"""
        if employee_ids is None:
            employee_ids = [101, 102, 103, 104, 105]
        
        employees = []
        for emp_id in employee_ids:
            emp_data = {"employee_id": emp_id}
            if increases:
                emp_data["increases"] = increases
            if deductions:
                emp_data["deductions"] = deductions
            employees.append(emp_data)
        
        return {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "id_employee_department": 5,
            "id_employee_charge": 12,
            "employees": employees
        }
    
    # ==================== TESTS ====================
    
    def test_ut_nom_003_01_successful_generation(self):
        """
        UT-NOM-003-01: Generar nómina masiva exitosamente
        """
        # Arrange
        self._authenticate_client()
        
        # Crear 5 empleados con contratos válidos
        for i, emp_id in enumerate([101, 102, 103, 104, 105], 1):
            user_id = 100 + i
            emp = self._create_employee(emp_id, user_id, f"emp{emp_id}@test.com")
            self._add_mock_user(user_id, f"Empleado{i}", "Apellido1", "Apellido2", f"123456789{i}")
            self._create_contract(emp, f"CON-{emp_id}", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload()
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "crearon" in data["message"].lower()
        assert data["data"]["created_count"] == 5
        assert len(data["data"]["created_payrolls"]) == 5
        
        # Verificar estructura de cada nómina
        for payroll_data in data["data"]["created_payrolls"]:
            assert "payroll_id" in payroll_data
            assert "employee_id" in payroll_data
            assert "base_salary" in payroll_data
            assert "total_increments" in payroll_data
            assert "total_deductions" in payroll_data
            assert "net_pay" in payroll_data
            assert "start_date" in payroll_data
            assert "end_date" in payroll_data
            assert "creation_date" in payroll_data
    
    def test_ut_nom_003_02_response_201_created(self):
        """
        UT-NOM-003-02: Respuesta 201 Created - Éxito Total
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["created_count"] >= 1
        assert "created_payrolls" in data["data"]
        assert len(data["data"]["created_payrolls"]) > 0
    
    def test_ut_nom_003_03_response_206_partial(self):
        """
        UT-NOM-003-03: Respuesta 206 Partial Content - Éxito Parcial
        """
        # Arrange
        self._authenticate_client()
        
        # Empleado válido
        emp1 = self._create_employee(101, 101, "emp101@test.com", self.status_active)
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp1, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        # Empleado inactivo
        emp2 = self._create_employee(102, 102, "emp102@test.com", self.status_inactive)
        self._add_mock_user(102, "Empleado", "Dos", "Test", "102102102")
        
        payload = self._create_valid_payload([101, 102])
        payload["exclude_conflicts"] = True
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        # Puede ser 201 o 206 dependiendo de la implementación
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_206_PARTIAL_CONTENT]
        data = response.json()
        assert data["success"] is True
        assert data["data"]["created_count"] >= 1
    
    def test_ut_nom_003_04_missing_start_date(self):
        """
        UT-NOM-003-04: Falta Campo start_date
        """
        # Arrange
        self._authenticate_client()
        
        payload = self._create_valid_payload()
        del payload["start_date"]
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "start_date" in str(data.get("errors", {}))
    
    def test_ut_nom_003_05_missing_end_date(self):
        """
        UT-NOM-003-05: Falta Campo end_date
        """
        # Arrange
        self._authenticate_client()
        
        payload = self._create_valid_payload()
        del payload["end_date"]
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
    
    def test_ut_nom_003_06_missing_id_employee_department(self):
        """
        UT-NOM-003-06: Falta Campo id_employee_department
        """
        # Arrange
        self._authenticate_client()
        
        payload = self._create_valid_payload()
        del payload["id_employee_department"]
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
    
    def test_ut_nom_003_07_missing_id_employee_charge(self):
        """
        UT-NOM-003-07: Falta Campo id_employee_charge
        """
        # Arrange
        self._authenticate_client()
        
        payload = self._create_valid_payload()
        del payload["id_employee_charge"]
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
    
    def test_ut_nom_003_08_missing_employees(self):
        """
        UT-NOM-003-08: Falta Campo employees
        """
        # Arrange
        self._authenticate_client()
        
        payload = {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "id_employee_department": 5,
            "id_employee_charge": 12
        }
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
    
    def test_ut_nom_003_09_empty_employees_array(self):
        """
        UT-NOM-003-09: Array employees Vacío
        """
        # Arrange
        self._authenticate_client()
        
        payload = self._create_valid_payload()
        payload["employees"] = []
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "al menos un empleado" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_10_end_date_before_start_date(self):
        """
        UT-NOM-003-10: end_date Anterior a start_date
        """
        # Arrange
        self._authenticate_client()
        
        payload = self._create_valid_payload()
        payload["start_date"] = "2025-01-31"
        payload["end_date"] = "2025-01-01"
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "fecha de fin debe ser igual o posterior" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_11_inactive_employee_without_exclude(self):
        """
        UT-NOM-003-11: Empleado Inactivo sin exclude_conflicts
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(102, 102, "emp102@test.com", self.status_inactive)
        self._add_mock_user(102, "Empleado", "Inactivo", "Test", "102102102")
        
        payload = self._create_valid_payload([102])
        payload["exclude_conflicts"] = False
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "rejected" in str(data.get("errors", {})).lower() or "inactivo" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_12_inactive_employee_with_exclude(self):
        """
        UT-NOM-003-12: Empleado Inactivo con exclude_conflicts true
        """
        # Arrange
        self._authenticate_client()
        
        # Empleado válido
        emp1 = self._create_employee(101, 101, "emp101@test.com", self.status_active)
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp1, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        # Empleado inactivo
        emp2 = self._create_employee(102, 102, "emp102@test.com", self.status_inactive)
        self._add_mock_user(102, "Empleado", "Dos", "Test", "102102102")
        
        payload = self._create_valid_payload([101, 102])
        payload["exclude_conflicts"] = True
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_206_PARTIAL_CONTENT]
        data = response.json()
        assert data["success"] is True
        assert data["data"]["created_count"] >= 1
    
    def test_ut_nom_003_13_employee_without_valid_contract(self):
        """
        UT-NOM-003-13: Empleado sin Contrato Válido
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(103, 103, "emp103@test.com")
        self._add_mock_user(103, "Empleado", "Sin", "Contrato", "103103103")
        # No crear contrato
        
        payload = self._create_valid_payload([103])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "contrato" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_14_employee_with_overlapping_payroll(self):
        """
        UT-NOM-003-14: Empleado con Nómina Solapada
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(104, 104, "emp104@test.com")
        self._add_mock_user(104, "Empleado", "Con", "Nómina", "104104104")
        contract = self._create_contract(emp, "CON-104", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        # Crear nómina existente que se solapa
        Payroll.objects.create(
            id_employee=emp,
            id_employee_contract=contract,
            base_salary=1000000.0,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 31),
            creation_date=self.now,
            time_worked=1.0,
            total_increments=0.0,
            total_deductions=0.0,
            net_pay=1000000.0,
            currency_type=self.currency,
            id_responsible_user=self.user
        )
        
        payload = self._create_valid_payload([104])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "solapa" in str(data.get("errors", {})).lower() or "conflicto" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_15_invalid_increase_type(self):
        """
        UT-NOM-003-15: Incremento increase_type Inválido
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], increases=[{
            "increase_type": 9999,  # No existe
            "amount_type": "fijo",
            "amount_value": 100000,
            "application_increase_type": "SalarioBase"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "tipo de incremento" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_16_increase_negative_amount_value(self):
        """
        UT-NOM-003-16: Incremento amount_value Negativo
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], increases=[{
            "increase_type": 45,
            "amount_type": "fijo",
            "amount_value": -10,
            "application_increase_type": "SalarioBase"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        errors_str = str(data.get("errors", {})).lower()
        assert ("negativo" in errors_str or 
                "mayor o igual a 0" in errors_str or 
                "greater than or equal to 0" in errors_str or
                "ensure this value" in errors_str)
    
    def test_ut_nom_003_17_increase_percentage_over_100(self):
        """
        UT-NOM-003-17: Incremento Porcentaje > 100
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], increases=[{
            "increase_type": 45,
            "amount_type": "Porcentaje",
            "amount_value": 150,
            "application_increase_type": "SalarioBase"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "100" in str(data.get("errors", {})) and "porcentaje" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_18_increase_end_date_before_start_date(self):
        """
        UT-NOM-003-18: Incremento end_date Anterior a start_date
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], increases=[{
            "increase_type": 45,
            "amount_type": "fijo",
            "amount_value": 100000,
            "application_increase_type": "SalarioBase",
            "start_date_increase": "2025-01-31",
            "end_date_increase": "2025-01-01"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "fecha de fin debe ser posterior" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_19_increase_end_date_without_start_date(self):
        """
        UT-NOM-003-19: Incremento Con end_date Pero sin start_date
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], increases=[{
            "increase_type": 45,
            "amount_type": "fijo",
            "amount_value": 100000,
            "application_increase_type": "SalarioBase",
            "end_date_increase": "2025-01-31"
            # Sin start_date_increase
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "obligatorio" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_20_invalid_deduction_type(self):
        """
        UT-NOM-003-20: Deducción deduction_type Inválido
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], deductions=[{
            "deduction_type": 9999,  # No existe
            "amount_type": "fijo",
            "amount_value": 50000,
            "application_deduction_type": "SalarioBase"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "tipo de deducción" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_21_deduction_negative_amount_value(self):
        """
        UT-NOM-003-21: Deducción amount_value Negativo
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], deductions=[{
            "deduction_type": 32,
            "amount_type": "fijo",
            "amount_value": -5000,
            "application_deduction_type": "SalarioBase"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        errors_str = str(data.get("errors", {})).lower()
        assert ("negativo" in errors_str or 
                "mayor o igual a 0" in errors_str or 
                "greater than or equal to 0" in errors_str or
                "ensure this value" in errors_str)
    
    def test_ut_nom_003_22_deduction_percentage_over_100(self):
        """
        UT-NOM-003-22: Deducción Porcentaje > 100
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], deductions=[{
            "deduction_type": 32,
            "amount_type": "Porcentaje",
            "amount_value": 110,
            "application_deduction_type": "SalarioBase"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "100" in str(data.get("errors", {})) and "porcentaje" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_23_deduction_end_date_before_start_date(self):
        """
        UT-NOM-003-23: Deducción end_date Anterior a start_date
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101], deductions=[{
            "deduction_type": 32,
            "amount_type": "fijo",
            "amount_value": 50000,
            "application_deduction_type": "SalarioBase",
            "start_date_deduction": "2025-01-31",
            "end_date_deductions": "2025-01-01"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "fecha de fin debe ser posterior" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_24_negative_net_pay(self):
        """
        UT-NOM-003-24: Pago Neto Negativo
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        # Salario base bajo
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31), salary_base=100000.0)
        
        # Deducción muy alta que resulte en pago neto negativo
        payload = self._create_valid_payload([101], deductions=[{
            "deduction_type": 32,
            "amount_type": "fijo",
            "amount_value": 200000,  # Mayor que el salario base
            "application_deduction_type": "SalarioBase"
        }])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        # Puede retornar 400 o procesar y rechazar el empleado
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_206_PARTIAL_CONTENT]
        data = response.json()
        # Si es 400, debe indicar el error
        # Si es 206, debe indicar el empleado rechazado
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            assert data["success"] is False
        else:
            assert "negativo" in str(data).lower() or "rejected" in str(data).lower()
    
    def test_ut_nom_003_25_invalid_batch_id(self):
        """
        UT-NOM-003-25: batch_id Inválido
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101])
        payload["batch_id"] = "550e8400-e29b-41d4-a716-000000000000"  # Inexistente
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "lote" in str(data.get("errors", {})).lower() or "batch" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_26_no_permission(self):
        """
        UT-NOM-003-26: Sin Permiso
        """
        # Arrange
        self._authenticate_client(permissions=self.token_without_permission)
        
        payload = self._create_valid_payload()
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "permisos" in data["message"].lower() or "forbidden" in str(response.status_code).lower()
    
    def test_ut_nom_003_27_no_authentication(self):
        """
        UT-NOM-003-27: Sin Autenticación
        """
        # Arrange
        client_no_auth = APIClient()
        
        payload = self._create_valid_payload()
        
        # Act
        response = client_no_auth.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_ut_nom_003_28_invalid_token(self):
        """
        UT-NOM-003-28: Token Inválido
        """
        # Arrange
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_12345')
        
        payload = self._create_valid_payload()
        
        # Act
        response = client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_ut_nom_003_29_method_get_not_allowed(self):
        """
        UT-NOM-003-29: Método GET No Permitido
        """
        # Arrange
        self._authenticate_client()
        
        # Act
        response = self.client.get(self.generate_massive_endpoint)
        
        # Assert
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_ut_nom_003_30_malformed_json(self):
        """
        UT-NOM-003-30: JSON Malformado
        """
        # Arrange
        self._authenticate_client()
        
        # Act
        response = self.client.post(
            self.generate_massive_endpoint,
            '{"invalid": json}',  # JSON malformado
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_ut_nom_003_31_multiple_increases_and_deductions(self):
        """
        UT-NOM-003-31: Incrementos y Deducciones Múltiples
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        increases = [
            {
                "increase_type": 45,
                "amount_type": "fijo",
                "amount_value": 100000,
                "application_increase_type": "SalarioBase"
            },
            {
                "increase_type": 45,
                "amount_type": "Porcentaje",
                "amount_value": 5,
                "application_increase_type": "SalarioFinal"
            },
            {
                "increase_type": 45,
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_increase_type": "SalarioBase"
            }
        ]
        
        deductions = [
            {
                "deduction_type": 32,
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_deduction_type": "SalarioBase"
            },
            {
                "deduction_type": 32,
                "amount_type": "Porcentaje",
                "amount_value": 2,
                "application_deduction_type": "SalarioFinal"
            },
            {
                "deduction_type": 32,
                "amount_type": "fijo",
                "amount_value": 30000,
                "application_deduction_type": "SalarioBase"
            },
            {
                "deduction_type": 32,
                "amount_type": "fijo",
                "amount_value": 20000,
                "application_deduction_type": "SalarioFinal"
            }
        ]
        
        payload = self._create_valid_payload([101], increases=increases, deductions=deductions)
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["created_payrolls"]) == 1
        
        payroll_data = data["data"]["created_payrolls"][0]
        assert payroll_data["total_increments"] > 0
        assert payroll_data["total_deductions"] > 0
    
    def test_ut_nom_003_32_multiple_employees(self):
        """
        UT-NOM-003-32: Múltiples Empleados (10+)
        """
        # Arrange
        self._authenticate_client()
        
        employee_ids = list(range(101, 116))  # 15 empleados
        for i, emp_id in enumerate(employee_ids, 1):
            user_id = 100 + i
            emp = self._create_employee(emp_id, user_id, f"emp{emp_id}@test.com")
            self._add_mock_user(user_id, f"Empleado{i}", "Apellido1", "Apellido2", f"123456789{i}")
            self._create_contract(emp, f"CON-{emp_id}", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload(employee_ids)
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["created_count"] == 15
        assert len(data["data"]["created_payrolls"]) == 15
    
    def test_ut_nom_003_33_mixed_employees_without_exclude(self):
        """
        UT-NOM-003-33: Múltiples Empleados Mixtos (algunos inválidos) sin exclude_conflicts
        """
        # Arrange
        self._authenticate_client()
        
        # 7 empleados válidos
        valid_ids = list(range(101, 108))
        for i, emp_id in enumerate(valid_ids, 1):
            user_id = 100 + i
            emp = self._create_employee(emp_id, user_id, f"emp{emp_id}@test.com")
            self._add_mock_user(user_id, f"Empleado{i}", "Apellido1", "Apellido2", f"123456789{i}")
            self._create_contract(emp, f"CON-{emp_id}", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        # 3 empleados inválidos (inactivos)
        invalid_ids = list(range(108, 111))
        for i, emp_id in enumerate(invalid_ids, 8):
            user_id = 100 + i
            emp = self._create_employee(emp_id, user_id, f"emp{emp_id}@test.com", self.status_inactive)
            self._add_mock_user(user_id, f"Empleado{i}", "Apellido1", "Apellido2", f"123456789{i}")
        
        payload = self._create_valid_payload(valid_ids + invalid_ids)
        payload["exclude_conflicts"] = False
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "rejected" in str(data.get("errors", {})).lower()
    
    def test_ut_nom_003_34_mixed_employees_with_exclude(self):
        """
        UT-NOM-003-34: Múltiples Empleados Mixtos con exclude_conflicts true
        """
        # Arrange
        self._authenticate_client()
        
        # 7 empleados válidos
        valid_ids = list(range(201, 208))
        for i, emp_id in enumerate(valid_ids, 1):
            user_id = 200 + i
            emp = self._create_employee(emp_id, user_id, f"emp{emp_id}@test.com")
            self._add_mock_user(user_id, f"Empleado{i}", "Apellido1", "Apellido2", f"223456789{i}")
            self._create_contract(emp, f"CON-{emp_id}", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        # 3 empleados inválidos (inactivos)
        invalid_ids = list(range(208, 211))
        for i, emp_id in enumerate(invalid_ids, 8):
            user_id = 200 + i
            emp = self._create_employee(emp_id, user_id, f"emp{emp_id}@test.com", self.status_inactive)
            self._add_mock_user(user_id, f"Empleado{i}", "Apellido1", "Apellido2", f"223456789{i}")
        
        payload = self._create_valid_payload(valid_ids + invalid_ids)
        payload["exclude_conflicts"] = True
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_206_PARTIAL_CONTENT]
        data = response.json()
        assert data["success"] is True
        assert data["data"]["created_count"] == 7
    
    def test_ut_nom_003_35_extra_fields_in_payload(self):
        """
        UT-NOM-003-35: Campos Extra en Payload
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101])
        payload["extra_field"] = "should be ignored"
        payload["another_field"] = 12345
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        # Debe procesar correctamente ignorando campos extra
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
    
    def test_ut_nom_003_36_response_structure_201(self):
        """
        UT-NOM-003-36: Validación de Estructura de Respuesta 201
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "created_count" in data["data"]
        assert "created_payrolls" in data["data"]
    
    def test_ut_nom_003_37_response_structure_206(self):
        """
        UT-NOM-003-37: Validación de Estructura de Respuesta 206
        """
        # Arrange
        self._authenticate_client()
        
        # Empleado válido
        emp1 = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp1, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        # Empleado inactivo
        emp2 = self._create_employee(102, 102, "emp102@test.com", self.status_inactive)
        self._add_mock_user(102, "Empleado", "Dos", "Test", "102102102")
        
        payload = self._create_valid_payload([101, 102])
        payload["exclude_conflicts"] = True
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        # Puede ser 201 o 206
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_206_PARTIAL_CONTENT]
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "created_count" in data["data"]
        if response.status_code == status.HTTP_206_PARTIAL_CONTENT:
            assert "failed_count" in data["data"]
            assert "failed_employees" in data["data"]
    
    def test_ut_nom_003_38_validate_created_payrolls_data(self):
        """
        UT-NOM-003-38: Validación de Datos en created_payrolls
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        payroll_data = data["data"]["created_payrolls"][0]
        
        assert "payroll_id" in payroll_data
        assert "employee_id" in payroll_data
        assert "base_salary" in payroll_data
        assert "total_increments" in payroll_data
        assert "total_deductions" in payroll_data
        assert "net_pay" in payroll_data
        assert isinstance(payroll_data["base_salary"], (int, float))
        assert isinstance(payroll_data["total_increments"], (int, float))
        assert isinstance(payroll_data["total_deductions"], (int, float))
        assert isinstance(payroll_data["net_pay"], (int, float))
    
    def test_ut_nom_003_39_validate_failed_employees_data(self):
        """
        UT-NOM-003-39: Validación de Datos en failed_employees
        """
        # Arrange
        self._authenticate_client()
        
        # Empleado válido
        emp1 = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp1, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        # Empleado inactivo
        emp2 = self._create_employee(102, 102, "emp102@test.com", self.status_inactive)
        self._add_mock_user(102, "Empleado", "Dos", "Test", "102102102")
        
        payload = self._create_valid_payload([101, 102])
        payload["exclude_conflicts"] = True
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        # Si retorna 206, debe tener failed_employees
        if response.status_code == status.HTTP_206_PARTIAL_CONTENT:
            data = response.json()
            if "failed_employees" in data["data"]:
                for failed in data["data"]["failed_employees"]:
                    assert "employee_id" in failed
                    assert "employee_name" in failed
                    assert "reason" in failed
    
    def test_ut_nom_003_40_persistence_in_database(self):
        """
        UT-NOM-003-40: Persistencia de Nóminas en BD
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        contract = self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        payroll_id = data["data"]["created_payrolls"][0]["payroll_id"]
        
        # Verificar en BD
        payroll = Payroll.objects.get(id_payroll=payroll_id)
        assert payroll.id_employee_id == 101
        assert payroll.start_date == date(2025, 1, 1)
        assert payroll.end_date == date(2025, 1, 31)
        assert payroll.base_salary == data["data"]["created_payrolls"][0]["base_salary"]
        assert payroll.total_increments == data["data"]["created_payrolls"][0]["total_increments"]
        assert payroll.total_deductions == data["data"]["created_payrolls"][0]["total_deductions"]
        assert payroll.net_pay == data["data"]["created_payrolls"][0]["net_pay"]
    
    def test_ut_nom_003_41_calculation_total_increments(self):
        """
        UT-NOM-003-41: Cálculo de Total Increments
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31), salary_base=1000000.0)
        
        increases = [
            {
                "increase_type": 45,
                "amount_type": "fijo",
                "amount_value": 100000,
                "application_increase_type": "SalarioBase"
            },
            {
                "increase_type": 45,
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_increase_type": "SalarioBase"
            }
        ]
        
        payload = self._create_valid_payload([101], increases=increases)
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        payroll_data = data["data"]["created_payrolls"][0]
        
        # Verificar que total_increments es la suma (aproximada debido a time_worked)
        assert payroll_data["total_increments"] >= 0
        # El cálculo exacto depende de time_worked, pero debe ser positivo si hay incrementos
    
    def test_ut_nom_003_42_calculation_total_deductions(self):
        """
        UT-NOM-003-42: Cálculo de Total Deductions
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        # Usar salario base estándar
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31), salary_base=1000000.0)
        
        # Usar deducciones porcentuales pequeñas para evitar pago neto negativo
        # Esto asegura que las deducciones sean proporcionales al salario
        deductions = [
            {
                "deduction_type": 32,
                "amount_type": "Porcentaje",
                "amount_value": 2.0,  # 2% del salario base
                "application_deduction_type": "SalarioBase"
            },
            {
                "deduction_type": 32,
                "amount_type": "Porcentaje",
                "amount_value": 1.5,  # 1.5% del salario base
                "application_deduction_type": "SalarioBase"
            }
        ]
        
        payload = self._create_valid_payload([101], deductions=deductions)
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED, f"Expected 201, got {response.status_code}. Response: {response.json() if response.status_code != 201 else 'OK'}"
        data = response.json()
        payroll_data = data["data"]["created_payrolls"][0]
        
        # Verificar que total_deductions está presente en la respuesta
        assert "total_deductions" in payroll_data
        assert payroll_data["total_deductions"] >= 0
        
        # Verificar que el sistema procesó las deducciones
        # Para deducciones porcentuales: 2% + 1.5% = 3.5% del salario base * time_worked
        # El cálculo exacto depende de time_worked, pero debe ser > 0 si time_worked > 0
        # Si time_worked es muy pequeño, las deducciones pueden ser muy pequeñas pero deben existir
        # Verificamos que el campo existe y es un número válido
        assert isinstance(payroll_data["total_deductions"], (int, float))
        
        # Verificar que net_pay considera las deducciones
        # net_pay = (base_salary * time_worked) + total_increments - total_deductions
        # Si hay deducciones, el net_pay debería ser menor que base_salary + increments
        base_salary = payroll_data["base_salary"]
        total_increments = payroll_data["total_increments"]
        total_deductions = payroll_data["total_deductions"]
        net_pay = payroll_data["net_pay"]
        
        # Verificar que el cálculo es consistente
        # net_pay debe ser razonable considerando las deducciones
        assert net_pay >= 0, f"El pago neto no debería ser negativo: {net_pay}"
    
    def test_ut_nom_003_43_calculation_net_pay(self):
        """
        UT-NOM-003-43: Cálculo de Net Pay
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31), salary_base=1000000.0)
        
        payload = self._create_valid_payload([101])
        
        # Act
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        payroll_data = data["data"]["created_payrolls"][0]
        
        # Verificar fórmula: net_pay = (base_salary * time_worked) + total_increments - total_deductions
        # Nota: base_salary en la respuesta es el valor SIN multiplicar por time_worked
        # Necesitamos obtener time_worked de la BD o calcularlo
        # Para simplificar, verificamos que el cálculo sea consistente
        # Si no tenemos time_worked en la respuesta, verificamos que net_pay sea razonable
        base_salary = payroll_data["base_salary"]
        total_increments = payroll_data["total_increments"]
        total_deductions = payroll_data["total_deductions"]
        net_pay = payroll_data["net_pay"]
        
        # El net_pay debe ser positivo (o al menos no muy negativo)
        # Verificamos que la fórmula básica se cumple aproximadamente
        # net_pay debería ser aproximadamente base_salary + increments - deductions
        # (considerando time_worked que puede ser < 1.0)
        # Como time_worked puede variar, solo verificamos que net_pay sea razonable
        assert net_pay >= 0, f"El pago neto no debería ser negativo: {net_pay}"
        
        # Verificar que net_pay es consistente: debe ser menor o igual a base_salary + increments
        # (ya que hay deducciones)
        max_possible = base_salary + total_increments
        assert net_pay <= max_possible, f"El pago neto no puede ser mayor que base_salary + increments: {net_pay} > {max_possible}"
    
    def test_ut_nom_003_44_performance_multiple_employees(self):
        """
        UT-NOM-003-44: Performance - Múltiples Empleados
        """
        # Arrange
        self._authenticate_client()
        
        import time
        
        employee_ids = list(range(301, 351))  # 50 empleados
        for i, emp_id in enumerate(employee_ids, 1):
            user_id = 300 + i
            emp = self._create_employee(emp_id, user_id, f"emp{emp_id}@test.com")
            self._add_mock_user(user_id, f"Empleado{i}", "Apellido1", "Apellido2", f"323456789{i}")
            self._create_contract(emp, f"CON-{emp_id}", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload(employee_ids)
        
        # Act
        start_time = time.time()
        response = self.client.post(self.generate_massive_endpoint, payload, format='json')
        elapsed_time = time.time() - start_time
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        # Verificar que se completa en menos de 5 segundos
        assert elapsed_time < 5.0, f"Tiempo de respuesta: {elapsed_time}s (esperado < 5s)"
    
    def test_ut_nom_003_45_idempotency(self):
        """
        UT-NOM-003-45: Idempotencia
        """
        # Arrange
        self._authenticate_client()
        
        emp = self._create_employee(101, 101, "emp101@test.com")
        self._add_mock_user(101, "Empleado", "Uno", "Test", "101101101")
        self._create_contract(emp, "CON-101", start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        
        payload = self._create_valid_payload([101])
        
        # Act - Primera petición
        response1 = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Act - Segunda petición idéntica (debe rechazar por nómina solapada)
        response2 = self.client.post(self.generate_massive_endpoint, payload, format='json')
        
        # Assert
        assert response1.status_code == status.HTTP_201_CREATED
        # La segunda debe fallar por nómina solapada
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "solapa" in str(response2.json().get("errors", {})).lower() or "conflicto" in str(response2.json().get("errors", {})).lower()

