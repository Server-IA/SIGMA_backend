"""
UT-EMP-003: Pruebas unitarias para endpoint de detalle de empleado
Endpoint: GET /employees/{id}/detail/
Permiso requerido: 182 - Ver detalle de empleado
"""

import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock, patch

from users.models import User
from parameterization.models import (
    EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory, Types, Units, TypesCategory, UnitsCategory
)
from payroll.models import Employee, EmployeeNews, EmployeeContract


@pytest.mark.django_db
class TestEmployeeDetail:
    """Pruebas para el endpoint de detalle de empleado"""
    
    def detail_endpoint(self, employee_id):
        """Endpoint para detalle de empleado"""
        return f'/employees/{employee_id}/detail/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con permisos
        self.token_with_permission = self._token_with_permissions([182])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Mock del servicio externo de usuarios: patch the batch helper used by the view
        self.get_users_batch_patcher = patch('service_requests.utils.external_user_helper.get_users_info_batch')
        self.mock_get_users_batch = self.get_users_batch_patcher.start()
        # Also patch requests.post in case serializers call it directly
        self.mock_external_user_patcher = patch('requests.post')
        self.mock_post = self.mock_external_user_patcher.start()
        self._setup_mock_external_user_service()
        # Configure batch helper to return our mock users when called
        def _batch_side_effect(ids, request):
            result = {}
            for uid in ids:
                if uid in self.mock_users:
                    result[uid] = self.mock_users[uid]
            return result

        self.mock_get_users_batch.side_effect = _batch_side_effect
    
    def teardown_method(self):
        """Limpieza después de cada prueba"""
        self.mock_external_user_patcher.stop()
        self.get_users_batch_patcher.stop()
    
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
                       second_last_name: str, document_number: str, email: str = None):
        """Agrega un usuario al mock del servicio externo"""
        self.mock_users[user_id] = {
            "id": user_id,
            "name": name,
            "first_last_name": first_last_name,
            "second_last_name": second_last_name,
            "document_number": document_number,
            "email": email or f"user{user_id}@test.com",
            "document_type": "Cédula",
            "gender": "Masculino",
            "birth_date": "1990-01-01T00:00:00",
            "phone": "3001234567",
            "country": "Colombia",
            "state": "Antioquia",
            "city": 101,
            "address": "Calle Test 123"
        }
    
    def _setup_parametrization(self):
        """Crea los tipos y unidades necesarias para los tests"""
        try:
            # Categorías
            status_cat, _ = StatuesCategory.objects.get_or_create(id_statues_categories=1, defaults={"name": "Status", "description": "Status", "creation_date": self.now, "modification_date": self.now})
            types_cat, _ = TypesCategory.objects.get_or_create(id_types_categories=1, defaults={"name": "Types", "description": "Types", "creation_date": self.now, "modification_date": self.now})
            units_cat, _ = UnitsCategory.objects.get_or_create(id_units_categories=1, defaults={"name": "Units", "description": "Units", "creation_date": self.now, "modification_date": self.now})

            # Estados
            self.status_active, _ = Statues.objects.get_or_create(id_statues=1, defaults={"name": "Activo", "description": "Active", "id_statues_categories": status_cat, "creation_date": self.now, "modification_date": self.now})
            self.status_inactive, _ = Statues.objects.get_or_create(id_statues=2, defaults={"name": "Inactivo", "description": "Inactive", "id_statues_categories": status_cat, "creation_date": self.now, "modification_date": self.now})
            
            # Tipos
            self.contract_type, _ = Types.objects.get_or_create(
                id_types=1, 
                defaults={
                    "name": "Indefinido", 
                    "description": "Indefinido", 
                    "id_types_categories": types_cat, 
                    "creation_date": self.now, 
                    "modification_date": self.now,
                    "id_statues": self.status_active
                }
            )
            self.workday_type, _ = Types.objects.get_or_create(
                id_types=2, 
                defaults={
                    "name": "Completa", 
                    "description": "Completa", 
                    "id_types_categories": types_cat, 
                    "creation_date": self.now, 
                    "modification_date": self.now,
                    "id_statues": self.status_active
                }
            )
            self.work_mode_type, _ = Types.objects.get_or_create(
                id_types=3, 
                defaults={
                    "name": "Presencial", 
                    "description": "Presencial", 
                    "id_types_categories": types_cat, 
                    "creation_date": self.now, 
                    "modification_date": self.now,
                    "id_statues": self.status_active
                }
            )
            
            # Unidades
            self.currency_cop, _ = Units.objects.get_or_create(
                id_units=1, 
                defaults={
                    "name": "COP", 
                    # "description": "Pesos",  <-- Removed invalid field
                    "id_units_categories": units_cat, 
                    "creation_date": self.now, 
                    "modification_date": self.now,
                    "id_types": self.contract_type,
                    "id_statues": self.status_active
                }
            )

            # Departamento y Cargo
            self.dept, _ = EmployeeDepartment.objects.get_or_create(id_employee_department=1, defaults={"name": "Ventas", "id_statues": self.status_active, "creation_date": self.now, "modification_date": self.now})
            
            self.charge, _ = EmployeeCharge.objects.get_or_create(
                id_employee_charge=1, 
                defaults={
                    "name": "Vendedor", 
                    "contract_prefix": "CON",
                    "description": "Ventas", 
                    "id_employee_department": self.dept, 
                    "id_statues": self.status_active, 
                    "creation_date": self.now, 
                    "modification_date": self.now
                }
            )
        except Exception as e:
            print(f"\n\nERROR IN SETUP: {str(e)}\n\n")
            raise e

    def _create_employee(self, user_id: int = None, email: str = "test@test.com", employee_status: Statues = None) -> Employee:
        """Crea un empleado de prueba"""
        if employee_status is None:
            employee_status = self.status_active
        
        user = None
        if user_id:
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

    def _create_contract(self, employee, code="CON-001"):
        """Crea un contrato para el empleado"""
        return EmployeeContract.objects.create(
            contract_code=code,
            id_employee_charge=self.charge,
            id_employee_department=self.dept,
            id_employee=employee,
            description="Contrato prueba",
            contract_type=self.contract_type,
            start_date=self.now.date(),
            payment_frequency_type="mensual",
            salary_type="Mensual fijo",
            salary_base=1000000,
            currency_type=self.currency_cop,
            vacation_days=15,
            cumulative_vacation=False,
            maximum_disability_days=180,
            overtime=0,
            contract_status=self.status_active,
            secundary_petition=False,
            creation_date=self.now,
            id_responsible_user=self.user
        )

    def _create_news(self, employee, news_type="CREACION_EMPLEADO", description="Test news", days_ago=0):
        """Crea una novedad para el empleado"""
        news = EmployeeNews.objects.create(
            id_employee=employee,
            observation=description,
            news_type=news_type,
            id_responsible_user=self.user
        )
        # Forzar fecha (auto_now_add no se puede sobreescribir en create, hay que actualizar)
        news.news_date = self.now - timedelta(days=days_ago)
        news.save()
        return news

    def _authenticate_client(self, permissions=None):
        """Autentica el cliente con los permisos especificados"""
        if permissions is None:
            token = self.token_with_permission
        else:
            token = permissions
        # Use DRF test client's force_authenticate to set both user and token (request.auth)
        self.client.force_authenticate(user=self.user, token=token)
        # Also set Authorization header as fallback for any calls that read headers
        self.client.credentials(HTTP_AUTHORIZATION='Bearer mock_token')

    # ==================== TESTS ====================

    def test_ut_emp_003_01_full_detail(self):
        """
        UT-EMP-003-01: Visualización completa de detalle de empleado con datos completos
        """
        # Arrange
        self._authenticate_client()
        
        # 1. Crear empleado
        emp = self._create_employee(123, "full@test.com")
        self._add_mock_user(123, "Juan", "Veru", "Sarmiento", "1079172265")
        
        # 2. Crear contrato
        self._create_contract(emp, "CON-2025-0003-00")
        
        # 3. Crear novedades (historial)
        self._create_news(emp, "CREACION_EMPLEADO", "Creación de empleado", days_ago=1)
        self._create_news(emp, "ACTUALIZACION_EMPLEADO", "Actualización de datos", days_ago=0)
        
        # Act
        response = self.client.get(self.detail_endpoint(emp.id_employee))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True
        
        # Verificar personal_info
        personal = data["data"]["personal_info"]
        assert personal["id_user"] == 123
        assert "Juan" in personal["full_name"]
        assert personal["document_number"] == "1079172265"
        assert personal["email"] == "user123@test.com" # Mock email
        
        # Verificar contract_info
        contract = data["data"]["contract_info"]
        assert contract["contract_code"] == "CON-2025-0003-00"
        assert contract["status_name"] == "Activo"
        assert contract["charge_name"] == "Vendedor"
        
        # Verificar news_history
        history = data["data"]["news_history"]
        assert len(history) == 2
        # Orden descendente: primero la actualización (days_ago=0), luego creación (days_ago=1)
        assert history[0]["action"] == "Actualizar empleado"
        assert history[1]["action"] == "Creación de empleado"

    def test_ut_emp_003_02_no_user(self):
        """
        UT-EMP-003-02: Detalle empleado sin usuario asociado
        """
        # Arrange
        self._authenticate_client()
        
        # Crear empleado SIN usuario (id_user=None)
        emp = self._create_employee(user_id=None, email="local@test.com")
        
        # Act
        response = self.client.get(self.detail_endpoint(emp.id_employee))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        personal = data["data"]["personal_info"]
        # Campos externos deben ser null
        assert personal["full_name"] is None
        assert personal["document_number"] is None
        # Campos locales deben existir
        assert personal["email"] == "local@test.com"

    def test_ut_emp_003_03_no_contract(self):
        """
        UT-EMP-003-03: Empleado sin contrato activo o asociado
        """
        # Arrange
        self._authenticate_client()
        emp = self._create_employee(789, "nocontract@test.com")
        self._add_mock_user(789, "No", "Contract", "User", "789789789")
        
        # No creamos contrato
        
        # Act
        response = self.client.get(self.detail_endpoint(emp.id_employee))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        contract = data["data"]["contract_info"]
        assert contract["contract_code"] is None
        # Otros campos de contrato podrían ser null o defaults del empleado (cargo, depto)
        # El endpoint devuelve charge_name y department_name del empleado si no hay contrato?
        # La doc dice: "contract_code será null." y "contract_info con campos null o vacíos"
        # Pero charge_id y department_id están en Employee también.
        # Verificamos al menos contract_code
        assert contract.get("contract_code") is None

    def test_ut_emp_003_04_no_news(self):
        """
        UT-EMP-003-04: Historial de novedades vacío para empleado sin modificaciones
        """
        # Arrange
        self._authenticate_client()
        emp = self._create_employee(321, "nonews@test.com")
        self._add_mock_user(321, "No", "News", "User", "321321321")
        self._create_contract(emp, "CON-321")
        
        # No creamos novedades
        
        # Act
        response = self.client.get(self.detail_endpoint(emp.id_employee))
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        history = data["data"]["news_history"]
        assert isinstance(history, list)
        assert len(history) == 0

    def test_ut_emp_003_05_access_denied(self):
        """
        UT-EMP-003-05: Acceso denegado sin permiso 182
        """
        # Arrange
        self._authenticate_client(permissions=self.token_without_permission)
        emp = self._create_employee(123, "denied@test.com")
        
        # Act
        response = self.client.get(self.detail_endpoint(emp.id_employee))
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "No tiene permisos" in response.json()["message"]

    def test_ut_emp_003_06_not_found(self):
        """
        UT-EMP-003-06: Manejo de error 404 cuando empleado no existe
        """
        # Arrange
        self._authenticate_client()
        
        # Act
        response = self.client.get(self.detail_endpoint(999999))
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Empleado no encontrado" in response.json()["message"]

    def test_ut_emp_003_07_internal_error(self):
        """
        UT-EMP-003-07: Manejo de errores internos del servicio
        """
        # Arrange
        self._authenticate_client()
        emp = self._create_employee(555, "error@test.com")
        
        # Simular error en servicio externo: forzamos que el helper de batch lance
        # la excepción para que llegue hasta la vista si el código no la maneja.
        self.mock_get_users_batch.side_effect = Exception("External Service Error")
        # También dejamos el mock_post con excepción por compatibilidad
        self.mock_post.side_effect = Exception("External Service Error")
        
        # Act
        response = self.client.get(self.detail_endpoint(emp.id_employee))
        
        # Assert
        # El requerimiento dice HTTP 500 y mensaje claro
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["success"] is False
        assert "Ocurrió un error al procesar la solicitud" in data["message"]
