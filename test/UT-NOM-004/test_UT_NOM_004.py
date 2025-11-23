"""
UT-NOM-004: Pruebas unitarias para endpoint de empleados aplicables para nómina masiva
Endpoint: GET /api/payroll/payroll-applicable-employees/
Permiso requerido: 188 - payroll.massive_payroll
"""

import pytest
from datetime import datetime, date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock, patch

from users.models import User
from parameterization.models import (
    EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory,
    TypesCategory, Types, UnitsCategory, Units
)
from payroll.models import Employee, EmployeeContract


@pytest.mark.django_db
class TestPayrollApplicableEmployees:
    """Pruebas para el endpoint de empleados aplicables para nómina masiva"""
    
    @property
    def applicable_employees_endpoint(self):
        """Endpoint para listar empleados aplicables"""
        return '/employees/payroll-applicable-employees/'
    
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
        # Diccionario para almacenar usuarios mockeados
        self.mock_users = {}
        
        def mock_post_side_effect(url, *args, **kwargs):
            """Side effect para simular respuestas del servicio externo"""
            mock_response = Mock()
            mock_response.status_code = 200
            
            # Extraer IDs solicitados del body
            json_data = kwargs.get('json', {})
            requested_ids = json_data.get('ids', [])
            
            # Filtrar usuarios que coinciden con los IDs solicitados
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
        # Crear categoría de estados
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
        
        # Crear categorías para tipos
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
        
        # Crear tipos
        for type_id, cat in [(19, cat_15), (22, cat_16), (25, cat_17)]:
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
        
        # Crear categoría de unidades
        cat_10_units, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10,
            defaults={
                "name": "Currency Types",
                "description": "Currency",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear moneda
        self.currency, _ = Units.objects.get_or_create(
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
        self.dept1, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={
                "name": "Departamento IT",
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        self.dept2, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=2,
            defaults={
                "name": "Departamento RRHH",
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear cargos
        self.charge1, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=5,
            defaults={
                "name": "Desarrollador Senior",
                "description": "Cargo test",
                "id_employee_department": self.dept1,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        self.charge2, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=6,
            defaults={
                "name": "Analista de RRHH",
                "description": "Cargo test 2",
                "id_employee_department": self.dept2,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
    
    def _create_employee(self, user_id: int, email: str, 
                        employee_status: Statues = None,
                        charge: EmployeeCharge = None) -> Employee:
        """Crea un empleado de prueba"""
        if employee_status is None:
            employee_status = self.status_active
        if charge is None:
            charge = self.charge1
        
        user = self._ensure_user(user_id)
        employee = Employee.objects.create(
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
        start_date: date = None,
        end_date: date = None,
        contract_status: Statues = None
    ) -> EmployeeContract:
        """Crea un contrato de prueba"""
        if charge is None:
            charge = self.charge1
        if start_date is None:
            start_date = self.today
        if contract_status is None:
            contract_status = self.status_created
        
        contract = EmployeeContract.objects.create(
            contract_code=contract_code,
            id_employee_charge=charge,
            id_employee_department=charge.id_employee_department,
            id_employee=employee,
            description="Contrato de prueba",
            contract_type=Types.objects.get(id_types=19),
            start_date=start_date,
            end_date=end_date,
            payment_frequency_type="mensual",
            minimum_hours=8,
            workday_type=Types.objects.get(id_types=22),
            work_mode_type=Types.objects.get(id_types=25),
            salary_type="Mensual fijo",
            salary_base=100000.0,
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
    
    # ==================== TESTS ====================
    
    def test_ut_nom_004_01_successful_listing(self):
        """
        UT-NOM-004-01: Listado exitoso de empleados aplicables para nómina masiva
        
        Verifica que el endpoint retorna todos los empleados activos, con contrato vigente
        para el cargo y fechas seleccionados.
        """
        # Arrange: Crear empleados con contratos que cumplan y no cumplan condiciones
        self._authenticate_client()
        
        # Empleado 1: Activo, cargo correcto, contrato vigente
        emp1 = self._create_employee(101, "juan.perez@test.com", self.status_active, self.charge1)
        self._add_mock_user(101, "Juan", "Pérez", "García", "1234567890")
        contract1 = self._create_contract(
            emp1, 
            "CON-2025-0001-00",
            charge=self.charge1,
            start_date=date(2025, 10, 1),
            end_date=date(2025, 12, 31)
        )
        
        # Empleado 2: Activo, cargo correcto, contrato indefinido
        emp2 = self._create_employee(102, "maria.lopez@test.com", self.status_active, self.charge1)
        self._add_mock_user(102, "María", "López", "Martínez", "0987654321")
        contract2 = self._create_contract(
            emp2,
            "CON-2025-0002-00",
            charge=self.charge1,
            start_date=date(2025, 11, 1),
            end_date=None  # Contrato indefinido
        )
        
        # Empleado 3: Inactivo, NO debe aparecer
        emp3 = self._create_employee(103, "pedro.garcia@test.com", self.status_inactive, self.charge1)
        self._add_mock_user(103, "Pedro", "García", "Sánchez", "1111111111")
        contract3 = self._create_contract(
            emp3,
            "CON-2025-0003-00",
            charge=self.charge1,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 12, 31)
        )
        
        # Empleado 4: Activo, cargo diferente, NO debe aparecer
        emp4 = self._create_employee(104, "ana.martinez@test.com", self.status_active, self.charge2)
        self._add_mock_user(104, "Ana", "Martínez", "Ruiz", "2222222222")
        contract4 = self._create_contract(
            emp4,
            "CON-2025-0004-00",
            charge=self.charge2,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 12, 31)
        )
        
        # Act: Realizar GET con cargo y fechas válidas
        response = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-30'
        })
        
        # Assert: HTTP 200 OK, "success": true
        assert response.status_code == status.HTTP_200_OK, \
            f"Expected 200, got {response.status_code}. Response: {response.json() if response.content else 'empty'}"
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 2  # Solo emp1 y emp2
        
        # Verificar que solo aparecen los empleados correctos
        employee_ids = [emp["id_employee"] for emp in data["data"]]
        assert emp1.id_employee in employee_ids
        assert emp2.id_employee in employee_ids
        assert emp3.id_employee not in employee_ids  # Inactivo
        assert emp4.id_employee not in employee_ids  # Cargo diferente
        
        # Verificar estructura de campos
        for employee_data in data["data"]:
            assert "id_employee" in employee_data
            assert "id_user" in employee_data
            assert "document_number" in employee_data
            assert "full_name" in employee_data
            assert "charge_name" in employee_data
            assert "charge_id" in employee_data
            assert employee_data["charge_id"] == 5
            assert "status_id" in employee_data
            assert employee_data["status_id"] == 1
            assert "status_name" in employee_data
            assert "email" in employee_data
    
    def test_ut_nom_004_02_filter_active_only(self):
        """
        UT-NOM-004-02: Filtro por estado activo (solo empleados activos)
        
        Asegura que solo empleados con status_id = 1 aparecen en el listado.
        """
        # Arrange: Crear empleados activos e inactivos
        self._authenticate_client()
        
        # Empleado activo
        emp1 = self._create_employee(201, "activo@test.com", self.status_active, self.charge1)
        self._add_mock_user(201, "Empleado", "Activo", "Uno", "201201201")
        contract1 = self._create_contract(
            emp1,
            "CON-2025-0201-00",
            charge=self.charge1,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 12, 31)
        )
        
        # Empleado inactivo
        emp2 = self._create_employee(202, "inactivo@test.com", self.status_inactive, self.charge1)
        self._add_mock_user(202, "Empleado", "Inactivo", "Dos", "202202202")
        contract2 = self._create_contract(
            emp2,
            "CON-2025-0202-00",
            charge=self.charge1,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 12, 31)
        )
        
        # Act: GET con filtro
        response = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-30'
        })
        
        # Assert: Solo empleados activos
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 1
        
        # Verificar que todos tienen status_id = 1
        for employee_data in data["data"]:
            assert employee_data["status_id"] == 1
            assert employee_data["status_name"] == "Activo"
    
    def test_ut_nom_004_03_contract_date_validation(self):
        """
        UT-NOM-004-03: Validación de contratos con fechas extremas
        
        Verifica lógica de inclusión: contratos que empiezan antes de fecha_hasta
        y terminan después de fecha_desde (o son indefinidos).
        """
        # Arrange: Crear empleados con diferentes rangos de contratos
        self._authenticate_client()
        
        # Caso 1: Contrato que empieza antes y termina dentro del rango (DEBE APARECER)
        emp1 = self._create_employee(301, "emp1@test.com", self.status_active, self.charge1)
        self._add_mock_user(301, "Empleado", "Uno", "Test", "301301301")
        contract1 = self._create_contract(
            emp1,
            "CON-2025-0301-00",
            charge=self.charge1,
            start_date=date(2025, 10, 15),  # Antes de fecha_desde
            end_date=date(2025, 11, 15)     # Dentro del rango
        )
        
        # Caso 2: Contrato que empieza dentro y termina después del rango (DEBE APARECER)
        emp2 = self._create_employee(302, "emp2@test.com", self.status_active, self.charge1)
        self._add_mock_user(302, "Empleado", "Dos", "Test", "302302302")
        contract2 = self._create_contract(
            emp2,
            "CON-2025-0302-00",
            charge=self.charge1,
            start_date=date(2025, 11, 15),  # Dentro del rango
            end_date=date(2026, 1, 15)      # Después de fecha_hasta
        )
        
        # Caso 3: Contrato indefinido que empieza antes (DEBE APARECER)
        emp3 = self._create_employee(303, "emp3@test.com", self.status_active, self.charge1)
        self._add_mock_user(303, "Empleado", "Tres", "Test", "303303303")
        contract3 = self._create_contract(
            emp3,
            "CON-2025-0303-00",
            charge=self.charge1,
            start_date=date(2025, 10, 1),
            end_date=None  # Indefinido
        )
        
        # Caso 4: Contrato que termina antes de fecha_desde (NO DEBE APARECER)
        emp4 = self._create_employee(304, "emp4@test.com", self.status_active, self.charge1)
        self._add_mock_user(304, "Empleado", "Cuatro", "Test", "304304304")
        contract4 = self._create_contract(
            emp4,
            "CON-2025-0304-00",
            charge=self.charge1,
            start_date=date(2025, 9, 1),
            end_date=date(2025, 10, 31)  # Termina antes de fecha_desde
        )
        
        # Caso 5: Contrato que empieza después de fecha_hasta (NO DEBE APARECER)
        emp5 = self._create_employee(305, "emp5@test.com", self.status_active, self.charge1)
        self._add_mock_user(305, "Empleado", "Cinco", "Test", "305305305")
        contract5 = self._create_contract(
            emp5,
            "CON-2025-0305-00",
            charge=self.charge1,
            start_date=date(2026, 1, 1),  # Empieza después de fecha_hasta
            end_date=date(2026, 2, 28)
        )
        
        # Act: GET con fechas límite
        response = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-30'
        })
        
        # Assert: Solo los contratos que cruzan el rango aparecen
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 3  # emp1, emp2, emp3
        
        employee_ids = [emp["id_employee"] for emp in data["data"]]
        assert emp1.id_employee in employee_ids
        assert emp2.id_employee in employee_ids
        assert emp3.id_employee in employee_ids
        assert emp4.id_employee not in employee_ids  # Terminó antes
        assert emp5.id_employee not in employee_ids  # Empieza después
    
    def test_ut_nom_004_04_missing_parameters(self):
        """
        UT-NOM-004-04: Error por parámetros faltantes
        
        Si falta cargo_id, fecha_desde o fecha_hasta, el sistema debe devolver
        error y mensaje específico.
        """
        # Arrange: Usuario autenticado
        self._authenticate_client()
        
        # Act & Assert: Caso 1 - Falta cargo_id
        response1 = self.client.get(self.applicable_employees_endpoint, {
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-30'
        })
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        data1 = response1.json()
        assert "Los parámetros 'cargo_id', 'fecha_desde' y 'fecha_hasta' son requeridos" in data1["message"]
        
        # Act & Assert: Caso 2 - Falta fecha_desde
        response2 = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_hasta': '2025-12-30'
        })
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        data2 = response2.json()
        assert "Los parámetros 'cargo_id', 'fecha_desde' y 'fecha_hasta' son requeridos" in data2["message"]
        
        # Act & Assert: Caso 3 - Falta fecha_hasta
        response3 = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-11-01'
        })
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        data3 = response3.json()
        assert "Los parámetros 'cargo_id', 'fecha_desde' y 'fecha_hasta' son requeridos" in data3["message"]
        
        # Act & Assert: Caso 4 - Todos los parámetros faltantes
        response4 = self.client.get(self.applicable_employees_endpoint)
        assert response4.status_code == status.HTTP_400_BAD_REQUEST
        data4 = response4.json()
        assert "Los parámetros 'cargo_id', 'fecha_desde' y 'fecha_hasta' son requeridos" in data4["message"]
    
    def test_ut_nom_004_05_invalid_date_format_and_range(self):
        """
        UT-NOM-004-05: Validación formato de fechas y rango
        
        Verifica el manejo de fechas mal formateadas y rango inválido
        (fecha_desde > fecha_hasta).
        """
        # Arrange: Usuario autenticado con permiso correcto
        self._authenticate_client()
        
        # Act & Assert: Caso 1 - Fecha inválida (mes 13)
        response1 = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-13-01',
            'fecha_hasta': '2025-12-30'
        })
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        data1 = response1.json()
        assert "'fecha_desde' y 'fecha_hasta' deben tener el formato YYYY-MM-DD" in data1["message"]
        
        # Act & Assert: Caso 2 - Fecha inválida (día 32)
        response2 = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-32'
        })
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        data2 = response2.json()
        assert "'fecha_desde' y 'fecha_hasta' deben tener el formato YYYY-MM-DD" in data2["message"]
        
        # Act & Assert: Caso 3 - Formato incorrecto
        response3 = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '01-11-2025',  # Formato incorrecto
            'fecha_hasta': '2025-12-30'
        })
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        data3 = response3.json()
        assert "'fecha_desde' y 'fecha_hasta' deben tener el formato YYYY-MM-DD" in data3["message"]
        
        # Act & Assert: Caso 4 - Rango inválido (fecha_desde > fecha_hasta)
        response4 = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-12-31',
            'fecha_hasta': '2025-12-01'
        })
        assert response4.status_code == status.HTTP_400_BAD_REQUEST
        data4 = response4.json()
        assert "'fecha_desde' debe ser menor o igual a 'fecha_hasta'" in data4["message"]
    
    def test_ut_nom_004_06_nonexistent_cargo(self):
        """
        UT-NOM-004-06: Cargo inexistente retorna 404
        
        Solicitar un cargo_id inexistente debe retornar error 404 con mensaje claro.
        """
        # Arrange: Usuario autenticado
        self._authenticate_client()
        
        # Act: Realizar la solicitud con cargo_id inexistente
        response = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 9999,  # ID que no existe
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-30'
        })
        
        # Assert: HTTP 404 NOT FOUND, mensaje específico
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "El cargo especificado no existe" in data["message"]
    
    def test_ut_nom_004_07_access_denied(self):
        """
        UT-NOM-004-07: Acceso denegado sin autenticación o sin permiso
        
        Verifica que sin JWT o sin permiso 188 la respuesta sea error apropiado.
        """
        # Caso 1: Usuario sin permiso 188
        self._authenticate_client(permissions=self.token_without_permission)
        response1 = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-30'
        })
        
        assert response1.status_code == status.HTTP_403_FORBIDDEN
        data1 = response1.json()
        assert "No tiene permisos para la gestión de nómina masiva" in data1["message"]
        
        # Caso 2: Sin autenticación
        client_no_auth = APIClient()
        response2 = client_no_auth.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-30'
        })
        
        assert response2.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        data2 = response2.json()
        assert "message" in data2
    
    def test_ut_nom_004_08_empty_results(self):
        """
        UT-NOM-004-08: Respuesta exitosa vacía si no hay empleados elegibles
        
        Cuando ningún empleado cumple los criterios, el endpoint responde
        success true, data vacía y no lanza error.
        """
        # Arrange: Base de datos sin empleados elegibles para cargo y fechas dados
        self._authenticate_client()
        
        # Crear un empleado que NO cumple (cargo diferente)
        emp1 = self._create_employee(801, "test@test.com", self.status_active, self.charge2)
        self._add_mock_user(801, "Test", "User", "Test", "801801801")
        contract1 = self._create_contract(
            emp1,
            "CON-2025-0801-00",
            charge=self.charge2,  # Cargo diferente
            start_date=date(2025, 11, 1),
            end_date=date(2025, 12, 31)
        )
        
        # Act: GET normal con cargo que no tiene empleados
        response = self.client.get(self.applicable_employees_endpoint, {
            'cargo_id': 5,  # Cargo sin empleados
            'fecha_desde': '2025-11-01',
            'fecha_hasta': '2025-12-30'
        })
        
        # Assert: HTTP 200 OK, data: [], success: true
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert data["data"] == []
        assert isinstance(data["data"], list)

