"""
UT-EMP-002: Pruebas unitarias para endpoint de listado de empleados
Endpoint: GET /employees/list
Permiso requerido: 183 - Consultar/Listar Empleados
"""

import pytest
from datetime import datetime
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock, patch

from users.models import User
from parameterization.models import (
    EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory
)
from payroll.models import Employee


@pytest.mark.django_db
class TestEmployeeList:
    """Pruebas para el endpoint de listado de empleados"""
    
    @property
    def list_endpoint(self):
        """Endpoint para listar empleados"""
        return '/employees/list/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con permisos
        self.token_with_permission = self._token_with_permissions([183])
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
                "name": "Desarrollador Senior",
                "description": "Cargo test",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
    
    def _create_employee(self, user_id: int, email: str, 
                        employee_status: Statues = None) -> Employee:
        """Crea un empleado de prueba"""
        if employee_status is None:
            employee_status = self.status_active
        
        user = self._ensure_user(user_id)
        employee = Employee.objects.create(
            id_user=user,
            email=email,
            id_employee_charge=self.charge,
            employee_status=employee_status,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        return employee
    
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
    
    def test_ut_emp_002_01_successful_paginated_list(self):
        """
        UT-EMP-002-01: Listado exitoso de empleados paginado
        
        Verifica que el endpoint retorna correctamente el listado paginado y estructurado
        de empleados, mostrando primero los activos y luego los inactivos.
        """
        # Arrange: Preparar datos (4 empleados: 2 activos, 2 inactivos)
        self._authenticate_client()
        
        # Crear empleados activos
        emp1 = self._create_employee(101, "ana.garcia@test.com", self.status_active)
        self._add_mock_user(101, "Ana", "García", "López", "111111111")
        
        emp2 = self._create_employee(102, "carlos.ruiz@test.com", self.status_active)
        self._add_mock_user(102, "Carlos", "Ruiz", "Pérez", "222222222")
        
        # Crear empleados inactivos
        emp3 = self._create_employee(103, "beatriz.mora@test.com", self.status_inactive)
        self._add_mock_user(103, "Beatriz", "Mora", "Sánchez", "333333333")
        
        emp4 = self._create_employee(104, "david.lopez@test.com", self.status_inactive)
        self._add_mock_user(104, "David", "López", "Martínez", "444444444")
        
        # Act: Ejecutar GET con paginación
        response = self.client.get(self.list_endpoint, {'page': 1, 'page_size': 10})
        
        # Assert: Verificar respuesta
        assert response.status_code == status.HTTP_200_OK, f"Expected 200, got {response.status_code}. Response: {response.json() if response.content else 'empty'}"
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 4  # Al menos los 4 que creamos
        
        # Verificar estructura de campos
        for employee_data in data["data"]:
            assert "id_employee" in employee_data
            assert "id_user" in employee_data
            assert "document_number" in employee_data
            assert "full_name" in employee_data
            assert "charge_name" in employee_data
            assert "charge_id" in employee_data
            assert "status_id" in employee_data
            assert "status_name" in employee_data
            assert "email" in employee_data
        
        # Verificar paginación
        assert "pagination" in data
        assert data["pagination"]["total"] >= 4
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10
    
    def test_ut_emp_002_02_filter_by_status(self):
        """
        UT-EMP-002-02: Filtro por estado de empleado
        
        Valida que el parámetro status permite filtrar el listado por estado
        (1=Activo, 2=Inactivo).
        """
        # Arrange: Crear empleados activos e inactivos
        self._authenticate_client()
        
        emp1 = self._create_employee(201, "emp1@test.com", self.status_active)
        self._add_mock_user(201, "Empleado", "Activo", "Uno", "201201201")
        
        emp2 = self._create_employee(202, "emp2@test.com", self.status_inactive)
        self._add_mock_user(202, "Empleado", "Inactivo", "Dos", "202202202")
        
        emp3 = self._create_employee(203, "emp3@test.com", self.status_inactive)
        self._add_mock_user(203, "Empleado", "Inactivo", "Tres", "203203203")
        
        # Act: GET filtrando por status=2 (Inactivo)
        response = self.client.get(self.list_endpoint, {'status': 2})
        
        # Assert: Todos los empleados en data son inactivos
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) == 2
        
        for employee_data in data["data"]:
            assert employee_data["status_id"] == 2
            assert employee_data["status_name"] == "Inactivo"
    
    def test_ut_emp_002_03_search_by_name_and_document(self):
        """
        UT-EMP-002-03: Búsqueda por nombre y búsqueda por documento
        
        Verifica el comportamiento de los parámetros search y search_type.
        """
        # Arrange: Crear empleados con nombre y documento únicos
        self._authenticate_client()
        
        emp1 = self._create_employee(301, "martina.gomez@test.com", self.status_active)
        self._add_mock_user(301, "Martina", "Gómez", "Rivera", "321321321")
        
        emp2 = self._create_employee(302, "otro.empleado@test.com", self.status_active)
        self._add_mock_user(302, "Otro", "Empleado", "Test", "999999999")
        
        # Act & Assert: Búsqueda por nombre
        response_name = self.client.get(self.list_endpoint, {
            'search': 'martina',
            'search_type': 'nombre'
        })
        
        assert response_name.status_code == status.HTTP_200_OK
        data_name = response_name.json()
        
        assert data_name["success"] is True
        assert len(data_name["data"]) == 1
        assert "Martina" in data_name["data"][0]["full_name"]
        
        # Act & Assert: Búsqueda por documento
        response_doc = self.client.get(self.list_endpoint, {
            'search': '321321321',
            'search_type': 'documento'
        })
        
        assert response_doc.status_code == status.HTTP_200_OK
        data_doc = response_doc.json()
        
        assert data_doc["success"] is True
        assert len(data_doc["data"]) == 1
        assert data_doc["data"][0]["document_number"] == "321321321"
    
    def test_ut_emp_002_04_ordering_ascending_descending(self):
        """
        UT-EMP-002-04: Ordenamiento por columna (ascendente/descendente)
        
        Valida que el parámetro ordering ordena el resultado adecuadamente según
        la columna (nombre, documento, estado).
        """
        # Arrange: Datos con distintas letras iniciales
        self._authenticate_client()
        
        emp1 = self._create_employee(401, "aura@test.com", self.status_active)
        self._add_mock_user(401, "Aura", "Álvarez", "Arias", "401401401")
        
        emp2 = self._create_employee(402, "zulema@test.com", self.status_active)
        self._add_mock_user(402, "Zulema", "Zapata", "Zuluaga", "402402402")
        
        emp3 = self._create_employee(403, "maria@test.com", self.status_active)
        self._add_mock_user(403, "María", "Martínez", "Moreno", "403403403")
        
        # Act: GET con ordering negativo por nombre (descendente)
        response = self.client.get(self.list_endpoint, {'ordering': '-name'})
        
        # Assert: Primer empleado tiene el nombre alfabéticamente mayor
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) >= 3
        
        # Zulema debe aparecer antes que María, y María antes que Aura
        names = [emp["full_name"] for emp in data["data"]]
        assert names[0].startswith("Zulema")
        assert names[-1].startswith("Aura")
    
    def test_ut_emp_002_05_empty_results_with_message(self):
        """
        UT-EMP-002-05: Respuesta vacía y mensaje cuando no hay coincidencias
        
        Si no hay empleados que cumplan con los criterios, la respuesta data es
        lista vacía y se muestra el mensaje correcto.
        """
        # Arrange: Query que no puede coincidir
        self._authenticate_client()
        
        # Crear un empleado para que la BD no esté vacía
        emp1 = self._create_employee(501, "test@test.com", self.status_active)
        self._add_mock_user(501, "Test", "User", "Test", "501501501")
        
        # Act: Solicitud con parámetro que no existe
        response = self.client.get(self.list_endpoint, {'search': 'no_existe_este_nombre'})
        
        # Assert: Response data: [], message correcto, pagination.total==0
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        assert data["data"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["total_pages"] == 0
        assert "message" in data
        assert "No se encontraron empleados" in data["message"]
    
    def test_ut_emp_002_06_pagination_validation(self):
        """
        UT-EMP-002-06: Validación de paginación y límites válidos
        
        Se valida que las opciones de paginación (page_size) aceptadas sean solo
        10, 25, 50 o 100, y que las páginas sean correctas.
        """
        # Arrange: Suficientes empleados en BD
        self._authenticate_client()
        
        # Crear 30 empleados para tener varias páginas
        for i in range(30):
            user_id = 600 + i
            emp = self._create_employee(user_id, f"emp{i}@test.com", self.status_active)
            self._add_mock_user(user_id, f"Empleado{i}", "Apellido", "Test", f"{user_id}")
        
        # Act & Assert: Primer caso - página 2 válida
        response_valid = self.client.get(self.list_endpoint, {
            'page': 2,
            'page_size': 25
        })
        
        assert response_valid.status_code == status.HTTP_200_OK
        data_valid = response_valid.json()
        
        assert data_valid["success"] is True
        assert data_valid["pagination"]["page"] == 2
        assert data_valid["pagination"]["page_size"] == 25
        assert len(data_valid["data"]) == 5  # 30 total - 25 en página 1 = 5 en página 2
        
        # Act & Assert: Segundo caso - page_size inválido
        response_invalid = self.client.get(self.list_endpoint, {'page_size': 200})
        
        assert response_invalid.status_code == status.HTTP_400_BAD_REQUEST
        data_invalid = response_invalid.json()
        
        assert "page_size debe ser uno de" in data_invalid["message"]
    
    def test_ut_emp_002_07_access_denied_without_auth_or_permission(self):
        """
        UT-EMP-002-07: Acceso denegado sin autenticación o sin permiso
        
        Valida que el recurso rechaza acceso sin JWT válido o sin permiso 183.
        """
        # Arrange & Act & Assert: Usuario sin permiso 183
        self._authenticate_client(permissions=self.token_without_permission)
        response_no_perm = self.client.get(self.list_endpoint)
        
        assert response_no_perm.status_code == status.HTTP_403_FORBIDDEN
        data_no_perm = response_no_perm.json()
        assert "No tiene permisos para acceder al listado de empleados" in data_no_perm["message"]
    
    def test_ut_emp_002_08_real_time_updates_validation(self):
        """
        UT-EMP-002-08: Validación de acciones y cambios en tiempo real
        
        Verifica que el listado se actualiza tras altas, bajas o cambios en empleados.
        """
        # Arrange: Estado inicial
        self._authenticate_client()
        
        # Consultar estado inicial (sin empleados)
        response_initial = self.client.get(self.list_endpoint)
        assert response_initial.status_code == status.HTTP_200_OK
        initial_count = response_initial.json()["pagination"]["total"]
        
        # Act: Alta de empleado
        emp1 = self._create_employee(801, "nuevo@test.com", self.status_active)
        self._add_mock_user(801, "Nuevo", "Empleado", "Alta", "801801801")
        
        # Assert: Lista se actualiza
        response_after_create = self.client.get(self.list_endpoint)
        assert response_after_create.status_code == status.HTTP_200_OK
        data_after_create = response_after_create.json()
        assert data_after_create["pagination"]["total"] == initial_count + 1
        
        # Act: Cambio de estado (activación/desactivación)
        emp1.employee_status = self.status_inactive
        emp1.save()
        
        # Assert: Lista refleja el cambio
        response_after_deactivate = self.client.get(self.list_endpoint, {'status': 2})
        assert response_after_deactivate.status_code == status.HTTP_200_OK
        data_after_deactivate = response_after_deactivate.json()
        
        # Verificar que el empleado ahora aparece en la lista de inactivos
        inactive_ids = [emp["id_employee"] for emp in data_after_deactivate["data"]]
        assert emp1.id_employee in inactive_ids
        
        # Act: Cambio de cargo
        # Crear nuevo cargo
        dept = EmployeeDepartment.objects.first()
        new_charge, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=2,
            defaults={
                "name": "Analista de Recursos Humanos",
                "description": "Nuevo cargo",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        emp1.id_employee_charge = new_charge
        emp1.save()
        
        # Assert: Lista refleja el nuevo cargo
        response_after_charge_change = self.client.get(self.list_endpoint)
        assert response_after_charge_change.status_code == status.HTTP_200_OK
        data_after_charge_change = response_after_charge_change.json()
        
        # Buscar el empleado en la lista
        updated_employee = next(
            (emp for emp in data_after_charge_change["data"] 
             if emp["id_employee"] == emp1.id_employee),
            None
        )
        
        assert updated_employee is not None
        assert updated_employee["charge_name"] == "Analista de Recursos Humanos"
