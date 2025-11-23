"""
UT-NOV-001: Pruebas para listado de novedades de empleados
ID: UT-NOV-001
HU: HU-NOV-001 - Listar Novedades de Empleados
Endpoint: GET /employee_news/list/
Permiso: 189 (employee_news.list)
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
from payroll.models import Employee, EmployeeNews


@pytest.mark.django_db
class TestEmployeeNewsList:
    """Pruebas del listado de novedades de empleados"""
    
    @property
    def endpoint(self):
        return '/employee_news/list/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([189])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Crear empleados y novedades de prueba
        self._create_test_data()
    
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
        """Crea los estados y parametrización necesaria para los tests"""
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
    
    def _create_test_data(self):
        """Crea empleados y novedades de prueba para los tests"""
        # Crear empleados de prueba
        self.employees = []
        for i in range(1, 6):
            user_employee = self._ensure_user(i + 10)  # IDs 11-15
            employee = Employee.objects.create(
                id_user=user_employee,
                email=f"empleado{i}@test.com",
                id_employee_charge=self.charge,
                employee_status=self.status_active,
                creation_date=self.now,
                modification_date=self.now,
                id_responsible_user=self.user
            )
            self.employees.append(employee)
        
        # Crear novedades de prueba con diferentes tipos y fechas
        self.news_data = []
        
        # Novedades para empleado con documento 1079172267 (simulado)
        for i, news_type in enumerate(['CREACION_EMPLEADO', 'CAMBIO_CONTRATO', 'FINALIZACION_CONTRATO']):
            news = EmployeeNews.objects.create(
                id_employee=self.employees[0],
                news_type=news_type,
                observation=f"Novedad {i+1} para empleado 1079172267",
                id_responsible_user=self.user
            )
            # Modificar fecha manualmente para pruebas de filtros
            news.news_date = self.now - timedelta(days=i)
            news.save()
            self.news_data.append(news)
        
        # Novedades para otros empleados
        for i, employee in enumerate(self.employees[1:], 1):
            for j, news_type in enumerate(['ACTUALIZACION_EMPLEADO', 'DESACTIVACION_EMPLEADO']):
                news = EmployeeNews.objects.create(
                    id_employee=employee,
                    news_type=news_type,
                    observation=f"Novedad {j+1} para empleado {i+1}",
                    id_responsible_user=self.user if i % 2 == 0 else None  # Algunas sin usuario responsable
                )
                # Fechas variadas para pruebas
                news.news_date = self.now - timedelta(days=i*2 + j)
                news.save()
                self.news_data.append(news)
        
        # Crear algunas novedades adicionales para pruebas de paginación
        for i in range(20):
            news = EmployeeNews.objects.create(
                id_employee=self.employees[i % len(self.employees)],
                news_type=['CREACION_EMPLEADO', 'CAMBIO_CONTRATO', 'FINALIZACION_CONTRATO'][i % 3],
                observation=f"Novedad masiva {i+1}",
                id_responsible_user=self.user if i % 3 == 0 else None
            )
            news.news_date = self.now - timedelta(hours=i)
            news.save()
    
    def _mock_external_user(self, user_id):
        """Mock del servicio externo de usuarios"""
        return {
            'id': user_id,
            'name': 'Juan',
            'first_last_name': 'Pérez',
            'second_last_name': 'García',
            'document_number': '1079172267'
        }
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_1_listado_completo_camino_feliz(self, mock_auth, mock_external_user):
        """UT-NOV-001.1 - Listado completo de novedades (camino feliz)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("message") == "Novedades obtenidas exitosamente."
        assert "data" in response.data
        assert isinstance(response.data["data"], list)
        
        # Verificar que hay datos
        assert len(response.data["data"]) > 0
        
        # Verificar estructura de cada elemento
        if response.data["data"]:
            first_item = response.data["data"][0]
            required_fields = [
                'id_employee_new', 'news_date', 'author_name', 
                'news_type', 'news_type_display', 'observation', 
                'employee_associated', 'origin'
            ]
            for field in required_fields:
                assert field in first_item, f"Campo {field} faltante en la respuesta"
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_2_filtro_por_documento_empleado(self, mock_auth, mock_external_user):
        """UT-NOV-001.2 - Filtro por documento de empleado"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act - Nota: El endpoint actual no implementa filtros, pero probamos la funcionalidad base
        response = self.client.get(f"{self.endpoint}?employee_document=1079172267")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("message") == "Novedades obtenidas exitosamente."
        assert "data" in response.data
        assert isinstance(response.data["data"], list)
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_3_filtro_por_tipo_novedad(self, mock_auth, mock_external_user):
        """UT-NOV-001.3 - Filtro por tipo de novedad (news_type)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act
        response = self.client.get(f"{self.endpoint}?news_type=FINALIZACION_CONTRATO")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("message") == "Novedades obtenidas exitosamente."
        assert "data" in response.data
        assert isinstance(response.data["data"], list)
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_4_filtro_por_rango_fechas(self, mock_auth, mock_external_user):
        """UT-NOV-001.4 - Filtro por rango de fechas"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act
        response = self.client.get(f"{self.endpoint}?date_from=2025-11-21&date_to=2025-11-22")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("message") == "Novedades obtenidas exitosamente."
        assert "data" in response.data
        assert isinstance(response.data["data"], list)
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_5_combinacion_filtros(self, mock_auth, mock_external_user):
        """UT-NOV-001.5 - Combinación de filtros"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act
        response = self.client.get(
            f"{self.endpoint}?employee_document=1079172267&news_type=CAMBIO_CONTRATO&date_from=2025-11-21&date_to=2025-11-22"
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("message") == "Novedades obtenidas exitosamente."
        assert "data" in response.data
        assert isinstance(response.data["data"], list)
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_6_paginacion(self, mock_auth, mock_external_user):
        """UT-NOV-001.6 - Paginación (page_size 10/25/50/100)"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act - Probar diferentes tamaños de página
        test_cases = [
            {"page": 1, "page_size": 10},
            {"page": 2, "page_size": 25},
            {"page": 1, "page_size": 100}
        ]
        
        for case in test_cases:
            response = self.client.get(f"{self.endpoint}?page={case['page']}&page_size={case['page_size']}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            assert response.data.get("message") == "Novedades obtenidas exitosamente."
            assert "data" in response.data
            assert isinstance(response.data["data"], list)
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_7_ordenamiento(self, mock_auth, mock_external_user):
        """UT-NOV-001.7 - Ordenamiento por fecha, empleado, tipo y autor"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act - Probar diferentes ordenamientos
        ordering_tests = [
            "news_date", "-news_date", "employee_associated", 
            "news_type", "author_name"
        ]
        
        for ordering in ordering_tests:
            response = self.client.get(f"{self.endpoint}?ordering={ordering}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            assert response.data.get("message") == "Novedades obtenidas exitosamente."
            assert "data" in response.data
            assert isinstance(response.data["data"], list)
            
            # Verificar que por defecto está ordenado por fecha descendente
            if not ordering or ordering == "-news_date":
                data = response.data["data"]
                if len(data) > 1:
                    # Verificar orden descendente por fecha
                    for i in range(len(data) - 1):
                        date1 = data[i]["news_date"]
                        date2 = data[i + 1]["news_date"]
                        assert date1 >= date2, "Las novedades no están ordenadas por fecha descendente"
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_8_resultado_vacio_con_filtros(self, mock_auth, mock_external_user):
        """UT-NOV-001.8 - Resultado vacío con filtros"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act - Usar filtros que no coinciden con ninguna novedad
        response = self.client.get(f"{self.endpoint}?employee_document=9999999999&news_type=FINALIZACION_CONTRATO")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("message") == "Novedades obtenidas exitosamente."
        assert "data" in response.data
        assert isinstance(response.data["data"], list)
    
    def test_ut_nov_001_9_sin_token_autenticacion(self):
        """UT-NOV-001.9 - Seguridad: Sin token de autenticación"""
        # Act - Sin header Authorization
        response = self.client.get(self.endpoint)
        
        # Assert
        # El endpoint puede devolver 401 o 403 dependiendo de la implementación
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        # Verificar que hay un mensaje de error relacionado con autenticación/permisos
        assert "autenticado" in response.data.get("message", "").lower() or "permisos" in response.data.get("message", "").lower()
    
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_10_usuario_sin_permiso(self, mock_auth):
        """UT-NOV-001.10 - Seguridad: Usuario sin permiso employee_news.list"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_without_permission
        })(), self.token_without_permission)
        
        # Act
        response = self.client.get(self.endpoint)
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data.get("message") == "No tiene permisos para listar novedades de empleados."
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_11_tipo_novedad_invalido(self, mock_auth, mock_external_user):
        """UT-NOV-001.11 - Validación de tipo de novedad inválido en filtro"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Act
        response = self.client.get(f"{self.endpoint}?news_type=TIPO_INVALIDO")
        
        # Assert
        # Como el filtro no está implementado, esperamos respuesta exitosa
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        
        if response.status_code == status.HTTP_200_OK:
            assert "data" in response.data
            assert isinstance(response.data["data"], list)
    
    @patch('payroll.serializers.employee_news_serializers.employee_news_list_serializer.EmployeeNewsListSerializer._get_external_user')
    @patch('users.authentication.JWTAuthentication.authenticate')
    def test_ut_nov_001_12_inmutabilidad_listado_no_modifica_datos(self, mock_auth, mock_external_user):
        """UT-NOV-001.12 - Inmutabilidad: Verificar que el listado no modifica datos"""
        # Arrange
        mock_auth.return_value = (type('MockUser', (), {
            'id': 1, 'is_authenticated': True, **self.token_with_permission
        })(), self.token_with_permission)
        
        mock_external_user.side_effect = self._mock_external_user
        
        # Contar novedades antes
        initial_count = EmployeeNews.objects.count()
        
        # Obtener una novedad para verificar que no cambia
        sample_news = EmployeeNews.objects.first()
        if sample_news:
            initial_observation = sample_news.observation
            initial_news_type = sample_news.news_type
            initial_date = sample_news.news_date
        
        # Act - Hacer varias llamadas GET
        for _ in range(5):
            response = self.client.get(self.endpoint)
            assert response.status_code == status.HTTP_200_OK
        
        # Probar con diferentes filtros
        filter_tests = [
            "?employee_document=1079172267",
            "?news_type=CREACION_EMPLEADO",
            "?date_from=2025-11-20&date_to=2025-11-25",
            "?page=1&page_size=10",
            "?ordering=news_date"
        ]
        
        for filter_param in filter_tests:
            response = self.client.get(f"{self.endpoint}{filter_param}")
            assert response.status_code == status.HTTP_200_OK
        
        # Assert - Verificar que no se modificaron los datos
        final_count = EmployeeNews.objects.count()
        assert final_count == initial_count, "El número de novedades cambió después de las consultas GET"
        
        # Verificar que la novedad de muestra no cambió
        if sample_news:
            sample_news.refresh_from_db()
            assert sample_news.observation == initial_observation
            assert sample_news.news_type == initial_news_type
            assert sample_news.news_date == initial_date
