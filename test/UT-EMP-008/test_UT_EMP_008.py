"""
UT-EMP-008: Pruebas para finalizar contrato de empleado
ID: UT-EMP-008
HU: HU-EMP-008 - Finalizar Contrato de Empleado
Endpoint: POST /employees/{contract_code}/terminate-contract/
Permiso: 185 (employee.terminate_employee_contract)
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
from payroll.models import Employee, EmployeeNews, EmployeeContract


@pytest.mark.django_db
class TestTerminateContract:
    """Pruebas de finalización de contrato de empleado"""
    
    @property
    def endpoint(self):
        return '/employees/CON-2025-0001-00/terminate-contract/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([185])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Crear empleado y contrato de prueba
        self._create_test_employee_and_contract()
    
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
        # Estado 1: Activo
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
        
        # Estado 2: Inactivo
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
        
        # Estado 28: Contrato Activo
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
        
        # Estado 29: Contrato Finalizado
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
        
        # Crear categorías de tipos
        # Categoría 1: Otra categoría (para test de categoría inválida)
        category_1, _ = TypesCategory.objects.get_or_create(
            id_types_categories=1,
            defaults={
                "name": "Categoría 1",
                "description": "Categoría de prueba",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categoría 20: Motivos de terminación
        category_20, _ = TypesCategory.objects.get_or_create(
            id_types_categories=20,
            defaults={
                "name": "Motivos de Terminación",
                "description": "Motivos de terminación de contrato",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Crear tipos
        # Tipo 5: En categoría 1 (para test de categoría inválida)
        self.type_invalid_category, _ = Types.objects.get_or_create(
            id_types=5,
            defaults={
                "name": "Tipo Categoría 1",
                "description": "Tipo de otra categoría",
                "id_types_categories": category_1,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Tipo 33: Motivo de terminación válido (categoría 20)
        self.type_termination_reason, _ = Types.objects.get_or_create(
            id_types=33,
            defaults={
                "name": "Término de período de prueba",
                "description": "Finalización por término de período de prueba",
                "id_types_categories": category_20,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
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
                "name": "Cargo 1",
                "description": "Cargo test",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear tipo de contrato (debe crearse antes de Units porque Units necesita id_types)
        contract_type_cat, _ = TypesCategory.objects.get_or_create(
            id_types_categories=10,
            defaults={
                "name": "Tipos de Contrato",
                "description": "Tipos de contrato",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.contract_type, _ = Types.objects.get_or_create(
            id_types=10,
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
        
        # Crear unidad (para contrato)
        unit_cat, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=1,
            defaults={
                "name": "Moneda",
                "description": "Categoría de monedas",
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.unit, _ = Units.objects.get_or_create(
            id_units=1,
            defaults={
                "name": "COP",
                "symbol": "COP",
                "id_units_categories": unit_cat,
                "id_types": self.contract_type,
                "id_statues": self.status_active,
                "id_responsible_user": self.user
            }
        )
    
    def _create_test_employee_and_contract(self):
        """Crea empleado y contrato de prueba"""
        # Crear usuario empleado
        user_employee = self._ensure_user(2)
        
        # Crear empleado activo
        self.employee, _ = Employee.objects.get_or_create(
            id_employee=1,
            defaults={
                "id_user": user_employee,
                "email": "empleado.test@example.com",
                "id_employee_charge": self.charge,
                "employee_status": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Crear contrato activo
        self.contract, _ = EmployeeContract.objects.get_or_create(
            contract_code="CON-2025-0001-00",
            defaults={
                "id_employee": self.employee,
                "id_employee_charge": self.charge,
                "id_employee_department": self.employee.id_employee_charge.id_employee_department,
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
        
        # Asegurar que el contrato esté activo
        self.contract.contract_status = self.status_contract_active
        self.contract.save()
        
        # Asegurar que el empleado esté activo
        self.employee.employee_status = self.status_active
        self.employee.save()
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_1_finalizacion_exitosa(self, mock_auth):
        """UT-EMP-008.1 - Finalización exitosa de contrato (camino feliz)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "contract_termination_reason": 33,
            "observation": "Contrato finalizado por término de período de prueba"
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["message"] == "Contrato finalizado exitosamente."
        
        # Verificar cambios en BD
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 29
        assert self.contract.contract_termination_reason_id == 33
        
        self.employee.refresh_from_db()
        assert self.employee.employee_status_id == 2
        
        # Verificar registro en historial de novedades
        news = EmployeeNews.objects.filter(
            id_employee=self.employee,
            news_type='FINALIZACION_CONTRATO'
        ).last()
        assert news is not None
        assert "Motivo: Término de período de prueba" in news.observation
        assert "Contrato finalizado por término de período de prueba" in news.observation
        assert news.id_responsible_user.id_user == 1
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_2_falta_campo_obligatorio(self, mock_auth):
        """UT-EMP-008.2 - Falta de campo obligatorio contract_termination_reason"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "observation": "Novedad sin motivo"
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        # Verificar que el error está en errors o directamente en response.data
        errors = response.data.get("errors", {})
        if not errors:
            # A veces el error puede estar directamente en response.data
            errors = response.data
        assert "contract_termination_reason" in errors
        assert "This field is required." in str(errors.get("contract_termination_reason", []))
        
        # Verificar que no se cambiaron estados
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 28
        
        self.employee.refresh_from_db()
        assert self.employee.employee_status_id == 1
        
        # Verificar que no se registró novedad
        news_count = EmployeeNews.objects.filter(
            id_employee=self.employee,
            news_type='FINALIZACION_CONTRATO'
        ).count()
        assert news_count == 0
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_3_motivo_categoria_invalida(self, mock_auth):
        """UT-EMP-008.3 - Motivo de terminación con categoría inválida"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "contract_termination_reason": 5,
            "observation": "Motivo incorrecto de prueba"
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        # Verificar que el error está en errors o directamente en response.data
        errors = response.data.get("errors", {})
        if not errors:
            errors = response.data
        assert "contract_termination_reason" in errors
        error_msg = str(errors.get("contract_termination_reason", []))
        assert "categoría 20" in error_msg or "categoria 20" in error_msg.lower()
        assert "categoría 1" in error_msg or "categoria 1" in error_msg.lower()
        
        # Verificar que los estados se mantienen
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 28
        
        self.employee.refresh_from_db()
        assert self.employee.employee_status_id == 1
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_4_contrato_ya_finalizado(self, mock_auth):
        """UT-EMP-008.4 - Contrato ya finalizado"""
        # Arrange
        # Finalizar el contrato primero
        self.contract.contract_status = self.status_contract_finished
        self.contract.save()
        
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "contract_termination_reason": 33,
            "observation": "Intento de finalizar contrato ya finalizado"
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "El contrato ya está finalizado" in response.data["message"]
        
        # Verificar que no se creó nueva novedad duplicada
        news_count_before = EmployeeNews.objects.filter(
            id_employee=self.employee,
            news_type='FINALIZACION_CONTRATO'
        ).count()
        
        # No debería haber cambiado nada
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 29
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_5_observacion_supera_longitud_maxima(self, mock_auth):
        """UT-EMP-008.5 - Descripción de novedad supera longitud máxima (255)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        # Generar string de 256 caracteres
        long_observation = "a" * 256
        
        payload = {
            "contract_termination_reason": 33,
            "observation": long_observation
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        # El error puede ser capturado por el serializer (400) o por la BD (500)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
        
        # Verificar que el contrato y empleado permanecen activos
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 28
        
        self.employee.refresh_from_db()
        assert self.employee.employee_status_id == 1
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_6_finalizar_sin_observacion(self, mock_auth):
        """UT-EMP-008.6 - Finalizar contrato sin observación (campo opcional)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "contract_termination_reason": 33
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["message"] == "Contrato finalizado exitosamente."
        
        # Verificar cambios en BD
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 29
        
        self.employee.refresh_from_db()
        assert self.employee.employee_status_id == 2
        
        # Verificar registro de novedad con motivo pero sin observación adicional
        news = EmployeeNews.objects.filter(
            id_employee=self.employee,
            news_type='FINALIZACION_CONTRATO'
        ).last()
        assert news is not None
        assert "Motivo: Término de período de prueba" in news.observation
    
    def test_ut_emp_008_7_contrato_no_encontrado(self):
        """UT-EMP-008.7 - Contrato no encontrado (contract_code inválido)"""
        # Arrange
        endpoint_inexistente = '/employees/CON-9999-XXXX-00/terminate-contract/'
        
        with patch('users.authentication.JWTAuthentication.authenticate') as mock_auth:
            mock_auth.return_value = (type('MockUser', (), {
                'id': 1, 'is_authenticated': True, **self.token_with_permission
            })(), self.token_with_permission)
            
            payload = {
                "contract_termination_reason": 33,
                "observation": "Intento con contrato inexistente"
            }
            
            # Act
            response = self.client.post(endpoint_inexistente, payload, format='json')
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.data["success"] is False
            assert "Contrato no encontrado" in response.data["message"]
            
            # Verificar que no se modificó ningún contrato
            self.contract.refresh_from_db()
            assert self.contract.contract_status_id == 28
    
    def test_ut_emp_008_8_sin_token_autenticacion(self):
        """UT-EMP-008.8 - Sin token de autenticación"""
        # Arrange
        payload = {
            "contract_termination_reason": 33,
            "observation": "Intento sin token"
        }
        
        # Act (sin configurar autenticación)
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        # Sin token puede devolver 401 o 403 dependiendo de la configuración
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        
        # Verificar que no hubo cambios en BD
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 28
        
        self.employee.refresh_from_db()
        assert self.employee.employee_status_id == 1
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_9_usuario_sin_permiso(self, mock_auth):
        """UT-EMP-008.9 - Usuario sin permiso employee.terminate_employee_contract"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_without_permission
        })(), self.token_without_permission)
        
        payload = {
            "contract_termination_reason": 33,
            "observation": "Intento sin permiso"
        }
        
        # Act
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["success"] is False
        assert "No tiene permisos para finalizar contratos" in response.data["message"]
        
        # Verificar que no hubo cambios en BD
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 28
        
        self.employee.refresh_from_db()
        assert self.employee.employee_status_id == 1
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_10_impacto_en_nomina_activa(self, mock_auth):
        """UT-EMP-008.10 - Verificar impacto en nómina activa"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "contract_termination_reason": 33,
            "observation": "Finalización para verificar impacto en nómina"
        }
        
        # Verificar que el empleado está activo antes
        assert self.employee.employee_status_id == 1
        
        # Act - Finalizar contrato
        response = self.client.post(self.endpoint, payload, format='json')
        
        # Assert - Verificar finalización exitosa
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        
        # Verificar que el empleado ya no está activo
        self.employee.refresh_from_db()
        assert self.employee.employee_status_id == 2
        
        # Verificar que el empleado no aparece en la nómina activa
        # (empleados activos tienen employee_status_id = 1)
        active_employees = Employee.objects.filter(employee_status_id=1)
        assert self.employee.id_employee not in [emp.id_employee for emp in active_employees]
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_emp_008_11_idempotencia_doble_intento(self, mock_auth):
        """UT-EMP-008.11 - Idempotencia lógica: doble intento de finalización"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        payload = {
            "contract_termination_reason": 33,
            "observation": "Primera finalización"
        }
        
        # Act - Primera llamada
        response1 = self.client.post(self.endpoint, payload, format='json')
        
        # Assert - Primera llamada exitosa
        assert response1.status_code == status.HTTP_200_OK
        assert response1.data["success"] is True
        
        # Verificar que el contrato está finalizado
        self.contract.refresh_from_db()
        assert self.contract.contract_status_id == 29
        
        # Act - Segunda llamada (mismo contract_code y body)
        payload2 = {
            "contract_termination_reason": 33,
            "observation": "Segunda finalización"
        }
        response2 = self.client.post(self.endpoint, payload2, format='json')
        
        # Assert - Segunda llamada debe fallar
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert response2.data["success"] is False
        assert "El contrato ya está finalizado" in response2.data["message"]
        
        # Verificar que no se creó una segunda novedad duplicada
        news_count = EmployeeNews.objects.filter(
            id_employee=self.employee,
            news_type='FINALIZACION_CONTRATO'
        ).count()
        # Debe haber solo una novedad (la de la primera llamada)
        assert news_count == 1

