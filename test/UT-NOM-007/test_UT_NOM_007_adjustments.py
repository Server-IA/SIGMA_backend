"""
UT-NOM-007: Pruebas unitarias para endpoint de carga masiva de ajustes temporales
Endpoint: POST /temporary_adjustments/upload/
Permiso requerido: 188 - payroll.massive_payroll
"""

import pytest
import json
import io
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock, patch
import openpyxl
from openpyxl import Workbook

from users.models import User
from parameterization.models import (
    EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory,
    TypesCategory, Types, UnitsCategory, Units
)
from payroll.models import Employee, EmployeeContract, TemporaryPayrollAdjustment


@pytest.mark.django_db
class TestTemporaryAdjustmentsUpload:
    """Pruebas para el endpoint de carga masiva de ajustes temporales"""
    
    @property
    def upload_endpoint(self):
        """Endpoint para subir ajustes masivos"""
        return '/temporary_adjustments/upload/'
    
    # Columnas requeridas en el Excel
    EXCEL_COLUMNS = [
        'Identificación del empleado',
        'Nombre del empleado',
        'Nombre del ajuste',
        'Tipo de ajuste',
        'Tipo de monto',
        'Valor',
        'Aplicación',
        'Fecha de Inicio',
        'Fecha de Fin',
        'Cantidad',
        'Descripción',
    ]
    
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
        self.mock_users = {}
        
        def mock_post_side_effect(url, *args, **kwargs):
            """Side effect para simular respuestas del servicio externo"""
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
        
        # Crear categorías para tipos de contrato
        cat_15, _ = TypesCategory.objects.get_or_create(
            id_types_categories=15,
            defaults={
                "name": "Contract Types",
                "description": "Contract Types",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear categorías para ajustes (deducciones e incrementos)
        cat_18, _ = TypesCategory.objects.get_or_create(
            id_types_categories=18,
            defaults={
                "name": "Deducciones",
                "description": "Tipos de deducciones",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        cat_19, _ = TypesCategory.objects.get_or_create(
            id_types_categories=19,
            defaults={
                "name": "Incrementos",
                "description": "Tipos de incrementos",
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear tipos de ajustes parametrizados
        self.deduction_type, _ = Types.objects.get_or_create(
            id_types=100,
            defaults={
                "name": "Deducción de seguridad social",
                "description": "Deducción de seguridad social",
                "id_types_categories": cat_18,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        self.increment_type, _ = Types.objects.get_or_create(
            id_types=101,
            defaults={
                "name": "Incremento por antigüedad",
                "description": "Incremento por antigüedad",
                "id_types_categories": cat_19,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
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
        
        # Crear cargo
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
    
    def _create_employee(self, user_id: int, email: str, document_number: str,
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
        
        # Agregar mock de usuario externo
        self._add_mock_user(
            user_id,
            "Usuario",
            "Test",
            "Apellido",
            document_number
        )
        
        return employee
    
    def _create_excel_file(self, rows_data):
        """Crea un archivo Excel en memoria con los datos proporcionados"""
        wb = Workbook()
        ws = wb.active
        
        # Agregar encabezados
        ws.append(self.EXCEL_COLUMNS)
        
        # Agregar filas de datos
        for row in rows_data:
            ws.append(row)
        
        # Guardar en memoria
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        return SimpleUploadedFile(
            "ajustes_masivos.xlsx",
            excel_file.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
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
    
    def test_ut_nom_007_01_successful_upload(self):
        """
        UT-NOM-007-01: Carga exitosa de ajustes masivos válidos
        
        Verifica que el endpoint procesa correctamente un archivo Excel con filas válidas
        y carga los ajustes temporalmente en la base de datos.
        """
        # Arrange: Crear empleados
        self._authenticate_client()
        
        emp1 = self._create_employee(101, "emp1@test.com", "1079172265")
        emp2 = self._create_employee(102, "emp2@test.com", "1079172267")
        
        # Crear Excel con datos válidos
        start_date = date(2025, 11, 17)
        end_date = date(2025, 11, 20)
        
        excel_rows = [
            [
                "1079172265",  # Identificación
                "Juan Andres Veru Sarmiento",  # Nombre
                "Incremento por antigüedad",  # Nombre del ajuste
                "incremento",  # Tipo de ajuste
                "porcentaje",  # Tipo de monto
                20.0,  # Valor
                "salario base",  # Aplicación
                "2025-11-17 00:00:00",  # Fecha de Inicio
                "2025-11-20 00:00:00",  # Fecha de Fin
                1.20,  # Cantidad
                "Ajuste de prueba 1"  # Descripción
            ],
            [
                "1079172267",  # Identificación
                "Juan Pablo de la Cruz",  # Nombre
                "Deducción de seguridad social",  # Nombre del ajuste
                "deduccion",  # Tipo de ajuste
                "fijo",  # Tipo de monto
                100000.0,  # Valor
                "salario final",  # Aplicación
                "2025-11-17 00:00:00",  # Fecha de Inicio
                "2025-11-18 00:00:00",  # Fecha de Fin
                2.0,  # Cantidad
                "Ajuste de prueba 2"  # Descripción
            ]
        ]
        
        excel_file = self._create_excel_file(excel_rows)
        
        # Preparar employees JSON
        employees_json = json.dumps([
            {"id_employee": emp1.id_employee, "document_number": "1079172265"},
            {"id_employee": emp2.id_employee, "document_number": "1079172267"}
        ])
        
        # Act: Subir archivo
        response = self.client.post(
            self.upload_endpoint,
            {
                'file': excel_file,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'employees': employees_json
            },
            format='multipart'
        )
        
        # Assert: HTTP 200 OK, success=true
        assert response.status_code == status.HTTP_200_OK, \
            f"Expected 200, got {response.status_code}. Response: {response.json() if response.content else 'empty'}"
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # Verificar estadísticas
        assert data["data"]["total_rows"] == 2
        assert data["data"]["accepted_rows"] == 2
        assert data["data"]["rejected_rows"] == 0
        
        # Verificar que ambas filas fueron aceptadas
        results = data["data"]["results"]
        assert len(results) == 2
        assert all(r["status"] == "Aceptado" for r in results)
        
        # Verificar que se guardaron en la BD
        batch_id = data["data"]["batch_id"]
        temp_adjustments = TemporaryPayrollAdjustment.objects.filter(batch_id=batch_id)
        assert temp_adjustments.count() == 2
        
        # Verificar que tienen expires_at configurado (24 horas)
        for adj in temp_adjustments:
            assert adj.expires_at is not None
            assert adj.expires_at > timezone.now()
    
    def test_ut_nom_007_02_nonexistent_employee(self):
        """
        UT-NOM-007-02: Rechazo por empleado no existente
        
        Rechaza la carga si alguna fila tiene empleado no en la lista o no activo.
        """
        # Arrange: Crear solo un empleado
        self._authenticate_client()
        
        emp1 = self._create_employee(201, "emp201@test.com", "1111111111")
        
        # Crear Excel con un empleado válido y uno inválido
        start_date = date(2025, 11, 17)
        end_date = date(2025, 11, 20)
        
        excel_rows = [
            [
                "1111111111",  # Empleado válido
                "Empleado Válido",
                "Incremento por antigüedad",
                "incremento",
                "fijo",
                1000.0,
                "salario base",
                "2025-11-17 00:00:00",
                "2025-11-18 00:00:00",
                1.0,
                "Ajuste válido"
            ],
            [
                "9999999999",  # Empleado NO existente
                "Empleado Inválido",
                "Incremento por antigüedad",
                "incremento",
                "fijo",
                1000.0,
                "salario base",
                "2025-11-17 00:00:00",
                "2025-11-18 00:00:00",
                1.0,
                "Este debe ser rechazado"
            ]
        ]
        
        excel_file = self._create_excel_file(excel_rows)
        
        employees_json = json.dumps([
            {"id_employee": emp1.id_employee, "document_number": "1111111111"}
        ])
        
        # Act: Subir archivo
        response = self.client.post(
            self.upload_endpoint,
            {
                'file': excel_file,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'employees': employees_json
            },
            format='multipart'
        )
        
        # Assert: Carga parcial
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["success"] is True  # Carga parcial
        assert data["data"]["total_rows"] == 2
        assert data["data"]["accepted_rows"] == 1
        assert data["data"]["rejected_rows"] == 1
        
        # Verificar razón de rechazo
        results = data["data"]["results"]
        rejected_row = [r for r in results if r["status"] == "Rechazado"][0]
        assert "9999999999" in rejected_row["employee_identification"]
        assert "no está en la lista de empleados aplicables" in rejected_row["reason_rejection"]
    
    def test_ut_nom_007_03_unparametrized_adjustment(self):
        """
        UT-NOM-007-03: Rechazo por novedad no parametrizada
        
        Si novedad no existe en parametrización, archivo rechazado con motivo.
        """
        # Arrange
        self._authenticate_client()
        
        emp1 = self._create_employee(301, "emp301@test.com", "3333333333")
        
        start_date = date(2025, 11, 17)
        end_date = date(2025, 11, 20)
        
        excel_rows = [
            [
                "3333333333",
                "Empleado Test",
                "Ajuste No Parametrizado",  # Este ajuste NO existe en Types
                "incremento",
                "fijo",
                1000.0,
                "salario base",
                "2025-11-17 00:00:00",
                "2025-11-18 00:00:00",
                1.0,
                "Este debe ser rechazado"
            ]
        ]
        
        excel_file = self._create_excel_file(excel_rows)
        
        employees_json = json.dumps([
            {"id_employee": emp1.id_employee, "document_number": "3333333333"}
        ])
        
        # Act
        response = self.client.post(
            self.upload_endpoint,
            {
                'file': excel_file,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'employees': employees_json
            },
            format='multipart'
        )
        
        # Assert: Todas las filas rechazadas
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data["success"] is False
        assert data["data"]["rejected_rows"] == 1
        assert data["data"]["accepted_rows"] == 0
        
        # Verificar mensaje de error
        results = data["data"]["results"]
        assert results[0]["status"] == "Rechazado"
        assert "no está registrado en el sistema" in results[0]["reason_rejection"]
    
    def test_ut_nom_007_04_date_range_validation(self):
        """
        UT-NOM-007-04: Validación de fechas dentro del rango
        
        Fechas de inicio y fin deben estar dentro del rango start_date-end_date.
        """
        # Arrange
        self._authenticate_client()
        
        emp1 = self._create_employee(401, "emp401@test.com", "4444444444")
        
        start_date = date(2025, 11, 17)
        end_date = date(2025, 11, 20)
        
        excel_rows = [
            [
                "4444444444",
                "Empleado Test",
                "Incremento por antigüedad",
                "incremento",
                "fijo",
                1000.0,
                "salario base",
                "2025-11-10 00:00:00",  # Fecha FUERA del rango (antes)
                "2025-11-18 00:00:00",
                1.0,
                "Fecha de inicio fuera de rango"
            ],
            [
                "4444444444",
                "Empleado Test",
                "Incremento por antigüedad",
                "incremento",
                "fijo",
                1000.0,
                "salario base",
                "2025-11-18 00:00:00",
                "2025-11-30 00:00:00",  # Fecha FUERA del rango (después)
                1.0,
                "Fecha de fin fuera de rango"
            ]
        ]
        
        excel_file = self._create_excel_file(excel_rows)
        
        employees_json = json.dumps([
            {"id_employee": emp1.id_employee, "document_number": "4444444444"}
        ])
        
        # Act
        response = self.client.post(
            self.upload_endpoint,
            {
                'file': excel_file,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'employees': employees_json
            },
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data["success"] is False
        assert data["data"]["rejected_rows"] == 2
        
        # Verificar que ambas filas fueron rechazadas por fechas fuera de rango
        results = data["data"]["results"]
        for result in results:
            assert result["status"] == "Rechazado"
            assert "fuera del rango" in result["reason_rejection"]
    
    def test_ut_nom_007_05_percentage_validation(self):
        """
        UT-NOM-007-05: Validación valor porcentaje ≤ 100
        
        Filas con porcentaje mayor a 100 deben ser rechazadas con motivo.
        """
        # Arrange
        self._authenticate_client()
        
        emp1 = self._create_employee(501, "emp501@test.com", "5555555555")
        
        start_date = date(2025, 11, 17)
        end_date = date(2025, 11, 20)
        
        excel_rows = [
            [
                "5555555555",
                "Empleado Test",
                "Incremento por antigüedad",
                "incremento",
                "porcentaje",
                150.0,  # Porcentaje > 100 (INVÁLIDO)
                "salario base",
                "2025-11-17 00:00:00",
                "2025-11-18 00:00:00",
                1.0,
                "Porcentaje inválido"
            ]
        ]
        
        excel_file = self._create_excel_file(excel_rows)
        
        employees_json = json.dumps([
            {"id_employee": emp1.id_employee, "document_number": "5555555555"}
        ])
        
        # Act
        response = self.client.post(
            self.upload_endpoint,
            {
                'file': excel_file,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'employees': employees_json
            },
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data["success"] is False
        assert data["data"]["rejected_rows"] == 1
        
        results = data["data"]["results"]
        assert results[0]["status"] == "Rechazado"
        assert "no puede superar el 100%" in results[0]["reason_rejection"]
    
    def test_ut_nom_007_06_data_type_validation(self):
        """
        UT-NOM-007-06: Validación tipo de dato de columnas
        
        Se rechazan filas con tipos de datos incorrectos (no numéricos en números, etc).
        """
        # Arrange
        self._authenticate_client()
        
        emp1 = self._create_employee(601, "emp601@test.com", "6666666666")
        
        start_date = date(2025, 11, 17)
        end_date = date(2025, 11, 20)
        
        excel_rows = [
            [
                "6666666666",
                "Empleado Test",
                "Incremento por antigüedad",
                "incremento",
                "fijo",
                "NO_ES_NUMERO",  # Valor no numérico (INVÁLIDO)
                "salario base",
                "2025-11-17 00:00:00",
                "2025-11-18 00:00:00",
                1.0,
                "Valor inválido"
            ],
            [
                "6666666666",
                "Empleado Test",
                "Incremento por antigüedad",
                "incremento",
                "fijo",
                1000.0,
                "salario base",
                "2025-11-17 00:00:00",
                "2025-11-18 00:00:00",
                "NO_ES_NUMERO",  # Cantidad no numérica (INVÁLIDA)
                "Cantidad inválida"
            ]
        ]
        
        excel_file = self._create_excel_file(excel_rows)
        
        employees_json = json.dumps([
            {"id_employee": emp1.id_employee, "document_number": "6666666666"}
        ])
        
        # Act
        response = self.client.post(
            self.upload_endpoint,
            {
                'file': excel_file,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'employees': employees_json
            },
            format='multipart'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data["success"] is False
        assert data["data"]["rejected_rows"] == 2
        
        # Verificar que fueron rechazadas por tipos de datos incorrectos
        results = data["data"]["results"]
        assert all(r["status"] == "Rechazado" for r in results)
        # Verificar que los mensajes de error contienen información sobre tipos incorrectos
        assert any("numérico" in r["reason_rejection"].lower() for r in results)
    
    def test_ut_nom_007_07_missing_columns(self):
        """
        UT-NOM-007-07: Rechazo por columnas obligatorias faltantes
        
        Carga rechazada si faltan columnas obligatorias en Excel.
        """
        # Arrange
        self._authenticate_client()
        
        emp1 = self._create_employee(701, "emp701@test.com", "7777777777")
        
        start_date = date(2025, 11, 17)
        end_date = date(2025, 11, 20)
        
        # Crear Excel con columnas INCOMPLETAS
        wb = Workbook()
        ws = wb.active
        
        # Solo agregar ALGUNAS columnas (faltarán varias)
        incomplete_columns = [
            'Identificación del empleado',
            'Nombre del empleado',
            'Valor',  # Faltan muchas columnas requeridas
        ]
        ws.append(incomplete_columns)
        
        # Agregar fila de datos
        ws.append(["7777777777", "Empleado Test", 1000.0])
        
        # Guardar en memoria
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        excel_file_upload = SimpleUploadedFile(
            "incomplete.xlsx",
            excel_file.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        employees_json = json.dumps([
            {"id_employee": emp1.id_employee, "document_number": "7777777777"}
        ])
        
        # Act
        response = self.client.post(
            self.upload_endpoint,
            {
                'file': excel_file_upload,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'employees': employees_json
            },
            format='multipart'
        )
        
        # Assert: HTTP 400 (o 500) con mensaje sobre columnas faltantes
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
        data = response.json()
        
        assert data["success"] is False
        # Verificar que el error menciona columnas faltantes/requeridas
        error_message = data.get("message", "") + str(data.get("error", "")) + str(data.get("errors", ""))
        assert "columnas" in error_message.lower() or "column" in error_message.lower()
