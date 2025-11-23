"""
UT-EMP-005: Pruebas para endpoints de historial de contratos de empleados
# Sync trigger
ID: UT-EMP-005
Endpoints:
- GET /employees/{id_employee}/contract-history/ (Permiso 184)
- GET /employees/contract-detail-history/?contract_code=XXX (Permiso 184)
- GET /employees/{contract_code}/employee_contract_detail/ (Permiso 181)
"""

import pytest
from datetime import date, timedelta, datetime
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock, patch
from decimal import Decimal

from users.models import User
from parameterization.models import (
    TypesCategory, Types, UnitsCategory, Units, 
    EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory
)
from payroll.models import (
    Employee, EmployeeContract, EmployeeContractDeduction, 
    EmployeeContractIncrease, EmployeeContractPayment
)


@pytest.mark.django_db
class TestEmployeeContractHistory:
    """Pruebas de historial de contratos de empleados"""
    
    
    @property
    def contract_history_endpoint(self):
        """Endpoint para historial de contratos de un empleado"""
        return '/employees/{}/contract-history/'
    
    @property
    def contract_detail_history_endpoint(self):
        """Endpoint para historial de versiones de un contrato"""
        return '/employees/contract-detail-history/'
    
    @property
    def employee_contract_detail_endpoint(self):
        """Endpoint para detalle de un contrato"""
        return '/employees/{}/employee_contract_detail/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con permisos 184 y 181
        self.token_with_permissions = self._token_with_permissions([184, 181])
        self.token_without_permissions = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Mock del servicio externo de usuarios
        self.mock_external_user_patcher = patch('requests.post')
        self.mock_post = self.mock_external_user_patcher.start()
        self._setup_mock_external_user_service()
    
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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = True
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 1,
                    "name": "Juan Andres",
                    "first_last_name": "Veru",
                    "second_last_name": "Sarmiento"
                }
            ]
        }
        self.mock_post.return_value = mock_response
    
    def _setup_parametrization(self):
        """Crea los tipos y unidades necesarias para los tests"""
        # Crear categorías
        cat_15, _ = TypesCategory.objects.get_or_create(
            id_types_categories=15, 
            defaults={
                "name": "Contract Types", 
                "description": "Contract Types", 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        cat_16, _ = TypesCategory.objects.get_or_create(
            id_types_categories=16, 
            defaults={
                "name": "Workday Types", 
                "description": "Workday Types", 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        cat_17, _ = TypesCategory.objects.get_or_create(
            id_types_categories=17, 
            defaults={
                "name": "Work Mode Types", 
                "description": "Work Mode Types", 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        cat_18, _ = TypesCategory.objects.get_or_create(
            id_types_categories=18, 
            defaults={
                "name": "Deduction Types", 
                "description": "Deduction Types", 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        cat_19, _ = TypesCategory.objects.get_or_create(
            id_types_categories=19, 
            defaults={
                "name": "Increase Types", 
                "description": "Increase Types", 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        cat_10_units, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10, 
            defaults={
                "name": "Currency Types", 
                "description": "Currency", 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        # Crear status category
        status_cat, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1, 
            defaults={
                "name": "Status", 
                "description": "Status", 
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
        
        self.status_cancelled, _ = Statues.objects.get_or_create(
            id_statues=29,
            defaults={
                "name": "Anulada", 
                "description": "Cancelled", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        # Crear tipos
        for type_id, cat in [(19, cat_15), (22, cat_16), (25, cat_17), (29, cat_18), (30, cat_18), (31, cat_19), (32, cat_19)]:
            Types.objects.get_or_create(
                id_types=type_id,
                defaults={
                    "name": f"Type {type_id}", 
                    "description": f"Type {type_id}", 
                    "id_types_categories": cat, 
                    "id_statues": self.status_active, 
                    "creation_date": self.now, 
                    "modification_date": self.now
                }
            )
        
        # Crear moneda
        Units.objects.get_or_create(
            id_units=17,
            defaults={
                "name": "Dollar", 
                "symbol": "$", 
                "id_units_categories": cat_10_units, 
                "id_types": Types.objects.get(id_types=19), 
                "id_statues": self.status_active
            }
        )
        
        # Crear departamento
        dept, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={
                "name": "Dept 1", 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        
        # Crear cargo
        self.charge, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=1,
            defaults={
                "name": "Encargado de ventas",
                "description": "Cargo test",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
    
    def _create_employee(self, email: str) -> Employee:
        """Crea un empleado de prueba"""
        user = self._ensure_user(len(Employee.objects.all()) + 100)
        employee = Employee.objects.create(
            id_user=user,
            email=email,
            id_employee_charge=self.charge,
            employee_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        return employee
    

    def _create_contract(
        self, 
        employee: Employee, 
        contract_code: str,
        contract_status: Statues = None,
        secundary_petition: bool = False,
        creation_date: datetime = None
    ) -> EmployeeContract:
        """Crea un contrato de prueba"""
        if contract_status is None:
            contract_status = self.status_created
        
        if creation_date is None:
            creation_date = self.now
        
        contract = EmployeeContract.objects.create(
            contract_code=contract_code,
            id_employee_charge=self.charge,
            id_employee_department=self.charge.id_employee_department,
            id_employee=employee,
            description="Contrato de prueba",
            contract_type=Types.objects.get(id_types=19),
            start_date=self.today,
            end_date=None,
            payment_frequency_type="diario",
            minimum_hours=8,
            workday_type=Types.objects.get(id_types=22),
            work_mode_type=Types.objects.get(id_types=25),
            salary_type="Mensual fijo",
            salary_base=100000.0,
            currency_type=Units.objects.get(id_units=17),
            trial_period_days=30,
            vacation_days=15,
            vacation_frequency_days=360,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today + timedelta(days=7),
            maximum_disability_days=15,
            overtime=40.0,
            overtime_period="dia",
            notice_period_days=9,
            contract_status=contract_status,
            secundary_petition=secundary_petition,
            creation_date=creation_date,
            id_responsible_user=self.user
        )
        return contract
    
    def _add_deduction_to_contract(self, contract: EmployeeContract):
        """Agrega una deducción a un contrato"""
        EmployeeContractDeduction.objects.create(
            employee_contracts_contract_code=contract,
            deduction_type=Types.objects.get(id_types=29),
            amount_type="fijo",
            amount_value=10000.0,
            application_deduction_type="SalarioBase",
            start_date_deduction=self.today + timedelta(days=1),
            end_date_deductions=self.today + timedelta(days=10),
            description="deduccion 1",
            amount=1.0
        )
    
    def _add_increase_to_contract(self, contract: EmployeeContract):
        """Agrega un incremento a un contrato"""
        EmployeeContractIncrease.objects.create(
            employee_contracts_contract_code=contract,
            increase_type=Types.objects.get(id_types=31),
            amount_type="Porcentaje",
            amount_value=100.0,
            application_increase_type="SalarioBase",
            start_date_increase=self.today + timedelta(days=1),
            end_date_increase=self.today + timedelta(days=13),
            description="aumento 1",
            amount=None
        )
    
    def _authenticate_client(self, permissions=None):
        """Autentica el cliente con los permisos especificados"""
        if permissions is None:
            token = self.token_with_permissions
        else:
            token = permissions
            
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer mock_token')

    # ==================== TESTS ====================
    
    # ==================== TESTS ====================
    
    def test_ut_emp_005_01_contract_history_success(self):
        """
        UT-EMP-005-01: Visualización de historial de contratos de un empleado existente
        
        Verifica que el endpoint retorna correctamente todos los contratos históricos
        asociados al empleado, ordenados del más nuevo al más antiguo.
        """
        # Arrange
        self._authenticate_client()
        
        employee = self._create_employee("test_history@example.com")
        
        # Crear 3 contratos con diferentes fechas
        contract1 = self._create_contract(
            employee, 
            "CON-2025-0001-00",
            creation_date=self.now - timedelta(hours=3)
        )
        contract2 = self._create_contract(
            employee, 
            "CON-2025-0002-00",
            creation_date=self.now - timedelta(hours=2)
        )
        contract3 = self._create_contract(
            employee, 
            "CON-2025-0003-00",
            creation_date=self.now - timedelta(hours=1)
        )
        
        # Act: Ejecutar GET al endpoint
        endpoint = self.contract_history_endpoint.format(employee.id_employee)
        response = self.client.get(endpoint)
        
        # Assert: Verificar respuesta
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 3
        
        # Verificar orden descendente por creation_date
        assert data["data"][0]["contract_code"] == "CON-2025-0003-00"
        assert data["data"][1]["contract_code"] == "CON-2025-0002-00"
        assert data["data"][2]["contract_code"] == "CON-2025-0001-00"
        
        # Verificar campos completos
        for contract_data in data["data"]:
            assert "contract_code" in contract_data
            assert "start_date" in contract_data
            assert "creation_date" in contract_data
            assert "id_responsible_user" in contract_data
            assert "responsible_user_name" in contract_data
            assert "contract_status" in contract_data
            assert "contract_status_name" in contract_data
    
    def test_ut_emp_005_02_contract_detail_history_success(self):
        """
        UT-EMP-005-02: Visualización del historial de versiones/otrosí de un contrato
        
        Valida que el endpoint retorna todas las versiones, otrosí y finalizaciones
        asociadas a ese contrato específico.
        """
        # Arrange: Crear empleado y múltiples versiones de un contrato
        self._authenticate_client()
        employee = self._create_employee("test_versions@example.com")
        
        # Crear versiones del mismo contrato
        contract_v0 = self._create_contract(
            employee, 
            "CON-2025-0004-00",
            secundary_petition=False,
            creation_date=self.now - timedelta(hours=3)
        )
        contract_v1 = self._create_contract(
            employee, 
            "CON-2025-0004-01",
            secundary_petition=True,
            creation_date=self.now - timedelta(hours=2)
        )
        contract_v2 = self._create_contract(
            employee, 
            "CON-2025-0004-02",
            contract_status=self.status_cancelled,
            secundary_petition=True,
            creation_date=self.now - timedelta(hours=1)
        )
        
        # Act: Ejecutar GET al endpoint
        endpoint = self.contract_detail_history_endpoint
        response = self.client.get(endpoint, {"contract_code": "CON-2025-0004-01"})
        
        # Assert: Verificar respuesta
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 3
        
        # Verificar orden por versión
        assert data["data"][0]["contract_code"] == "CON-2025-0004-00"
        assert data["data"][1]["contract_code"] == "CON-2025-0004-01"
        assert data["data"][2]["contract_code"] == "CON-2025-0004-02"
        
        # Verificar campo secundary_petition
        assert data["data"][0]["secundary_petition"] is False
        assert data["data"][1]["secundary_petition"] is True
        assert data["data"][2]["secundary_petition"] is True
    
    def test_ut_emp_005_03_access_denied_no_permission(self):
        """
        UT-EMP-005-03: Acceso denegado si falta permiso contractual
        
        Valida que cualquier intento de acceder a los endpoints sin permiso
        employee.employee_contract_list es rechazado.
        """
        # Arrange: Crear empleado con contrato
        self._authenticate_client(permissions=self.token_without_permissions)
        employee = self._create_employee("test_noperm@example.com")
        contract = self._create_contract(employee, "CON-2025-0005-00")
        
        # Act & Assert: Intentar acceder sin autenticación (sin permisos)
        endpoint1 = self.contract_history_endpoint.format(employee.id_employee)
        response1 = self.client.get(endpoint1)
        assert response1.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        
        endpoint2 = self.contract_detail_history_endpoint
        response2 = self.client.get(endpoint2, {"contract_code": "CON-2025-0005-00"})
        assert response2.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        
        endpoint3 = self.employee_contract_detail_endpoint.format("CON-2025-0005-00")
        response3 = self.client.get(endpoint3)
        assert response3.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ut_emp_005_04_empty_history_no_contracts(self):
        """
        UT-EMP-005-04: Historial vacío para empleado sin contratos
        
        Verifica que para empleados sin contratos históricos, la respuesta
        contiene una lista vacía.
        """
        # Arrange: Crear empleado sin contratos
        self._authenticate_client()
        employee = self._create_employee("test_nocontracts@example.com")
        
        # Act: Consultar endpoint de historial
        endpoint = self.contract_history_endpoint.format(employee.id_employee)
        response = self.client.get(endpoint)
        
        # Assert: Verificar lista vacía
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 0
        assert isinstance(data["data"], list)
    
    def test_ut_emp_005_05_contract_detail_complete_fields(self):
        """
        UT-EMP-005-05: Contrato detalle: respuesta con todos los campos y tipos correctos
        
        Verifica que el endpoint de detalle retorna todos los campos y tipos
        según especificación.
        """
        # Arrange: Crear contrato con deducciones e incrementos
        self._authenticate_client()
        employee = self._create_employee("test_detail@example.com")
        contract = self._create_contract(employee, "CON-2025-0006-00")
        self._add_deduction_to_contract(contract)
        self._add_increase_to_contract(contract)
        
        # Agregar payment
        EmployeeContractPayment.objects.create(
            employee_contracts_contract_code=contract,
            id_day_of_week=None,
            date_payment=None
        )
        
        # Act: Ejecutar GET detalle
        endpoint = self.employee_contract_detail_endpoint.format("CON-2025-0006-00")
        response = self.client.get(endpoint)
        
        # Assert: Verificar campos y tipos
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Campos principales
        assert "contract_code" in data
        assert "id_employee_charge" in data
        assert "employee_charge_name" in data
        assert "description" in data
        assert "contract_type" in data
        assert "start_date" in data
        assert "salary_base" in data
        assert isinstance(data["salary_base"], (int, float))
        assert "contract_payments" in data
        assert isinstance(data["contract_payments"], list)
        assert "employee_contract_deductions" in data
        assert isinstance(data["employee_contract_deductions"], list)
        assert "employee_contract_increases" in data
        assert isinstance(data["employee_contract_increases"], list)
        
        # Verificar deducción
        if len(data["employee_contract_deductions"]) > 0:
            deduction = data["employee_contract_deductions"][0]
            assert "deduction_type" in deduction
            assert "amount_type" in deduction
            assert "amount_value" in deduction
            assert isinstance(deduction["amount_value"], (int, float))
        
        # Verificar incremento
        if len(data["employee_contract_increases"]) > 0:
            increase = data["employee_contract_increases"][0]
            assert "increase_type" in increase
            assert "amount_type" in increase
            assert "amount_value" in increase
    
    def test_ut_emp_005_06_history_with_cancelled_contracts(self):
        """
        UT-EMP-005-06: Historial con contratos anulados/cancelados
        
        Valida que el historial de contratos muestra de forma clara contratos
        con estado "Anulado" o "Cancelado".
        """
        # Arrange: Crear empleado con contratos activos y anulados
        self._authenticate_client()
        employee = self._create_employee("test_cancelled@example.com")
        
        contract1 = self._create_contract(
            employee, 
            "CON-2025-0007-00",
            contract_status=self.status_created
        )
        contract2 = self._create_contract(
            employee, 
            "CON-2025-0008-00",
            contract_status=self.status_cancelled
        )
        
        # Act: Consultar historial
        endpoint = self.contract_history_endpoint.format(employee.id_employee)
        response = self.client.get(endpoint)
        
        # Assert: Verificar que aparecen ambos contratos con estados correctos
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2
        
        # Buscar contrato anulado
        cancelled_contract = next(
            (c for c in data["data"] if c["contract_code"] == "CON-2025-0008-00"), 
            None
        )
        assert cancelled_contract is not None
        assert cancelled_contract["contract_status"] == 29
        assert cancelled_contract["contract_status_name"] == "Anulada"
    
    def test_ut_emp_005_07_strict_ordering_by_datetime(self):
        """
        UT-EMP-005-07: Ordenación estricta: fecha/hora y contratos múltiples
        
        Comprueba que el orden de los contratos históricos siempre es descendente
        por fecha/hora de "creation_date".
        """
        # Arrange: Crear contratos con diferentes horas
        self._authenticate_client()
        employee = self._create_employee("test_ordering@example.com")
        
        contract1 = self._create_contract(
            employee, 
            "CON-2025-0009-00",
            creation_date=self.now - timedelta(hours=5)
        )
        contract2 = self._create_contract(
            employee, 
            "CON-2025-0010-00",
            creation_date=self.now - timedelta(hours=3)
        )
        contract3 = self._create_contract(
            employee, 
            "CON-2025-0011-00",
            creation_date=self.now - timedelta(hours=1)
        )
        
        # Act: Consultar historial
        endpoint = self.contract_history_endpoint.format(employee.id_employee)
        response = self.client.get(endpoint)
        
        # Assert: Verificar orden descendente
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 3
        
        # El más reciente primero
        assert data["data"][0]["contract_code"] == "CON-2025-0011-00"
        assert data["data"][1]["contract_code"] == "CON-2025-0010-00"
        assert data["data"][2]["contract_code"] == "CON-2025-0009-00"
    
    def test_ut_emp_005_08_filter_by_employee_isolation(self):
        """
        UT-EMP-005-08: Filtro por empleado: no mezclar contratos de otros usuarios
        
        Valida que nunca aparecen contratos de otros empleados al consultar
        el historial de un empleado específico.
        """
        # Arrange: Crear dos empleados con sus contratos
        self._authenticate_client()
        employee1 = self._create_employee("employee1@example.com")
        employee2 = self._create_employee("employee2@example.com")
        
        contract1 = self._create_contract(employee1, "CON-2025-0012-00")
        contract2 = self._create_contract(employee2, "CON-2025-0013-00")
        
        # Act: Consultar historial del primer empleado
        endpoint = self.contract_history_endpoint.format(employee1.id_employee)
        response = self.client.get(endpoint)
        
        # Assert: Solo aparecen contratos del empleado 1
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["contract_code"] == "CON-2025-0012-00"
        
        # Verificar que no aparece el contrato del empleado 2
        contract_codes = [c["contract_code"] for c in data["data"]]
        assert "CON-2025-0013-00" not in contract_codes
    
    def test_ut_emp_005_09_nonexistent_contract_code(self):
        """
        UT-EMP-005-09: Error por contract_code inexistente (parámetro inválido)
        
        Prueba el manejo adecuado cuando se consulta historial de un código
        de contrato que no existe en base de datos.
        """
        # Arrange: No existe el contract_code
        self._authenticate_client()
        
        # Act: Consultar endpoint con dato inválido
        endpoint = self.contract_detail_history_endpoint
        response = self.client.get(endpoint, {"contract_code": "NO-EXISTE-999"})
        
        # Assert: Error controlado
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert "message" in data
    
    def test_ut_emp_005_10_cross_permissions_validation(self):
        """
        UT-EMP-005-10: Permisos cruzados: consulta detalle contrato con permiso alterno
        
        Asegura que para el endpoint de detalle de contrato, solo el permiso
        adecuado (employee.employee_contract_detail 181) da acceso.
        """
        # Arrange: Crear contrato
        # Usar token con permiso 184 (list) pero sin 181 (detail)
        token_partial = self._token_with_permissions([184])
        self._authenticate_client(permissions=token_partial)
        
        employee = self._create_employee("test_perms@example.com")
        contract = self._create_contract(employee, "CON-2025-0014-00")
        
        # Act: Hacer GET al endpoint de detalle sin autenticación
        endpoint = self.employee_contract_detail_endpoint.format("CON-2025-0014-00")
        response = self.client.get(endpoint)
        
        # Assert: Acceso denegado sin permiso 181
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        
        # Verificar mensaje de error
        if response.status_code == status.HTTP_403_FORBIDDEN:
            data = response.json()
            assert "message" in data
