"""
UT-EMP-009: Pruebas para actualizar empleado
ID: UT-EMP-009
HU: HU-EMP-009 - Actualizar Empleado
Endpoint: PATCH /employees/{id}/update-employee/
Permiso: 4 (users.edit)
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from users.models import User
from parameterization.models import TypesCategory, Types, UnitsCategory, Units, EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory
from payroll.models import Employee, EmployeeNews


@pytest.mark.django_db
class TestUpdateEmployee:
    """Pruebas de actualización de empleado"""
    
    @property
    def endpoint(self):
        return '/employees/1/update-employee/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([4])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Crear empleado de prueba
        self._create_test_employee()
    
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
        # Crear categorías de status
        status_cat, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1, 
            defaults={
                "name": "Status", 
                "description": "Status", 
                "creation_date": timezone.now(), 
                "modification_date": timezone.now()
            }
        )
        
        # Crear status activo
        self.status_active, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                "name": "Active", 
                "description": "Active", 
                "id_statues_categories": status_cat, 
                "creation_date": timezone.now(), 
                "modification_date": timezone.now()
            }
        )
        
        # Crear departamento
        dept, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={
                "name": "Dept 1", 
                "id_statues": self.status_active, 
                "creation_date": timezone.now(), 
                "modification_date": timezone.now()
            }
        )
        
        # Crear cargos
        self.charge1, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=1,
            defaults={
                "name": "Cargo 1",
                "description": "Cargo test 1",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": timezone.now(),
                "modification_date": timezone.now()
            }
        )
        
        self.charge2, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=2,
            defaults={
                "name": "Cargo 2",
                "description": "Cargo test 2",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": timezone.now(),
                "modification_date": timezone.now()
            }
        )
        
        self.charge3, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=3,
            defaults={
                "name": "Cargo 3",
                "description": "Cargo test 3",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": timezone.now(),
                "modification_date": timezone.now()
            }
        )
    
    def _create_test_employee(self):
        """Crea empleado de prueba con id=1"""
        user_employee = self._ensure_user(2)
        self.employee, _ = Employee.objects.get_or_create(
            id_employee=1,
            defaults={
                "id_user": user_employee,
                "email": "empleado.original@example.com",
                "id_employee_charge": self.charge1,
                "employee_status": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Crear empleado adicional para pruebas de email duplicado
        user_employee_b = self._ensure_user(3)
        Employee.objects.get_or_create(
            id_employee=2,
            defaults={
                "id_user": user_employee_b,
                "email": "empleado.yaexiste@example.com",
                "id_employee_charge": self.charge1,
                "employee_status": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_009_1_actualizacion_exitosa(self, mock_auth):
        """UT-EMP-009.1 - Actualización exitosa de empleado (camino feliz)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "email": "empleado.prueba@example.com",
            "id_employee_charge": 2,
            "observation": "Actualización de información del empleado"
        }
        
        # Act
        response = self.client.patch(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Empleado actualizado exitosamente."
        
        # Verificar cambios en BD
        self.employee.refresh_from_db()
        assert self.employee.email == "empleado.prueba@example.com"
        assert self.employee.id_employee_charge.id_employee_charge == 2
        
        # Verificar registro de novedad
        news = EmployeeNews.objects.filter(id_employee=self.employee).last()
        assert news is not None
        assert news.observation == "Actualización de información del empleado"
        assert news.news_type == "ACTUALIZACION_EMPLEADO"
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_009_2_email_duplicado(self, mock_auth):
        """UT-EMP-009.2 - Email duplicado"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "email": "empleado.yaexiste@example.com",
            "id_employee_charge": 2,
            "observation": "Cambio de correo a uno ya usado"
        }
        
        # Act
        response = self.client.patch(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert "Ya existe un empleado con este correo electrónico." in str(response.data["email"])
        
        # Verificar que no se modificó el email
        self.employee.refresh_from_db()
        assert self.employee.email == "empleado.original@example.com"
        
        # Verificar que no se registró novedad
        news_count = EmployeeNews.objects.filter(id_employee=self.employee).count()
        assert news_count == 0
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_009_3_falta_campo_obligatorio_observation(self, mock_auth):
        """UT-EMP-009.3 - Falta campo obligatorio observation"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "email": "empleado.nuevo@example.com",
            "id_employee_charge": 2
        }
        
        # Act
        response = self.client.patch(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "observation" in response.data
        assert "This field is required." in str(response.data["observation"])
        
        # Verificar que no se actualizó información en BD
        self.employee.refresh_from_db()
        assert self.employee.email == "empleado.original@example.com"
        assert self.employee.id_employee_charge.id_employee_charge == 1
        
        # Verificar que no se creó novedad
        news_count = EmployeeNews.objects.filter(id_employee=self.employee).count()
        assert news_count == 0
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_009_4_observacion_supera_longitud_maxima(self, mock_auth):
        """UT-EMP-009.4 - Observación supera longitud máxima (255)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        # Generar string de 256 caracteres
        long_observation = "a" * 256
        
        payload = {
            "email": "empleado.prueba@example.com",
            "id_employee_charge": 2,
            "observation": long_observation
        }
        
        # Act
        response = self.client.patch(self.endpoint, payload, format='json')
        
        # Assert
        # El error de longitud máxima puede ser capturado por la BD (500) o por el serializer (400)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
        
        # Verificar que no se actualizó el empleado
        self.employee.refresh_from_db()
        assert self.employee.email == "empleado.original@example.com"
        assert self.employee.id_employee_charge.id_employee_charge == 1
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_009_5_email_formato_invalido(self, mock_auth):
        """UT-EMP-009.5 - Email con formato inválido"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "email": "correo-invalido-sin-arroba",
            "id_employee_charge": 2,
            "observation": "Probando email inválido"
        }
        
        # Act
        response = self.client.patch(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        
        # Verificar que no se actualizó el correo en BD
        self.employee.refresh_from_db()
        assert self.employee.email == "empleado.original@example.com"
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_009_6_cambio_solo_cargo_sin_email(self, mock_auth):
        """UT-EMP-009.6 - Cambio solo de cargo sin email"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "id_employee_charge": 3,
            "observation": "Actualización de cargo del empleado"
        }
        
        # Act
        response = self.client.patch(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar cambios en BD
        self.employee.refresh_from_db()
        assert self.employee.id_employee_charge.id_employee_charge == 3
        assert self.employee.email == "empleado.original@example.com"  # Email permanece igual
        
        # Verificar registro de novedad
        news = EmployeeNews.objects.filter(id_employee=self.employee).last()
        assert news is not None
        assert news.observation == "Actualización de cargo del empleado"
        assert news.news_type == "ACTUALIZACION_EMPLEADO"
    
    def test_ut_emp_009_7_empleado_no_existe(self):
        """UT-EMP-009.7 - Empleado no existe"""
        # Arrange
        endpoint_inexistente = '/employees/9999/update-employee/'
        
        with patch('users.authentication.JWTAuthentication.authenticate') as mock_auth:
            mock_auth.return_value = (type('MockUser', (), {
                'id': 1, 'is_authenticated': True, **self.token_with_permission
            })(), self.token_with_permission)
            
            payload = {
                "email": "empleado.inexistente@example.com",
                "id_employee_charge": 2,
                "observation": "Intento de actualizar empleado inexistente"
            }
            
            # Act
            response = self.client.patch(endpoint_inexistente, payload, format='json')
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Empleado no encontrado." in str(response.data["message"])
    
    def test_ut_emp_009_8_sin_token_autenticacion(self):
        """UT-EMP-009.8 - Sin token de autenticación"""
        # Arrange
        payload = {
            "email": "empleado.prueba@example.com",
            "id_employee_charge": 2,
            "observation": "Intento sin token"
        }
        
        # Act (sin configurar autenticación)
        response = self.client.patch(self.endpoint, payload, format='json')
        
        # Assert
        # Sin token puede devolver 401 o 403 dependiendo de la configuración del sistema
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        
        # Verificar que no hubo cambios en BD
        self.employee.refresh_from_db()
        assert self.employee.email == "empleado.original@example.com"
        assert self.employee.id_employee_charge.id_employee_charge == 1
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_009_9_usuario_sin_permiso(self, mock_auth):
        """UT-EMP-009.9 - Usuario sin permiso users.edit"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_without_permission
        })(), self.token_without_permission)
        
        payload = {
            "email": "empleado.prueba@example.com",
            "id_employee_charge": 2,
            "observation": "Intento sin permiso"
        }
        
        # Act
        response = self.client.patch(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "No tiene permisos para actualizar empleados." in str(response.data["message"])
        
        # Verificar que no hubo cambios en BD
        self.employee.refresh_from_db()
        assert self.employee.email == "empleado.original@example.com"
        assert self.employee.id_employee_charge.id_employee_charge == 1
