"""
UT-NOV-004: Pruebas unitarias para endpoint de generación de informe PDF de historial de nóminas
Endpoint: POST /payroll_history_reports/generate/
Permiso requerido: 194 - payroll.history_report
"""

import pytest
import json
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
from payroll.models import (
    Employee, EmployeeContract, Payroll,
    PayrollIncrease, PayrollDeduction
)


@pytest.mark.django_db
class TestPayrollHistoryReportGeneration:
    """Pruebas para el endpoint de generación de informes PDF de historial de nóminas"""
    
    @property
    def generate_report_endpoint(self):
        """Endpoint para generar informe PDF"""
        return '/payroll_history_reports/generate/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con permisos
        self.token_with_permission = self._token_with_permissions([194])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Mock del servicio externo de usuarios (by-document endpoint)
        self.mock_external_user_patcher = patch('requests.get')
        self.mock_get = self.mock_external_user_patcher.start()
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
        """Configura el mock del servicio externo de usuarios (by-document endpoint)"""
        self.mock_users_by_document = {}
        
        def mock_get_side_effect(url, *args, **kwargs):
            """Side effect para simular respuestas del servicio externo by-document"""
            mock_response = Mock()
            
            # Extraer el número de documento de la URL
            # URL esperada: {base_url}/users/users/by-document/{document}
            if '/by-document/' in url:
                parts = url.split('/by-document/')
                if len(parts) == 2:
                    document = parts[1].strip('/')
                    
                    if document in self.mock_users_by_document:
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            "data": self.mock_users_by_document[document]
                        }
                        mock_response.content = True
                    else:
                        # Documento no encontrado
                        mock_response.status_code = 404
                        mock_response.json.return_value = {"message": "Not found"}
                        mock_response.content = False
                else:
                    mock_response.status_code = 404
                    mock_response.content = False
            else:
                mock_response.status_code = 404
                mock_response.content = False
            
            return mock_response
        
        self.mock_get.side_effect = mock_get_side_effect
    
    def _add_mock_user_by_document(self, document_number: str, user_id: int,
                                    name: str, first_last_name: str, second_last_name: str):
        """Agrega un usuario al mock del servicio externo by-document"""
        self.mock_users_by_document[document_number] = {
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
        
        # Categorías para incrementos y deducciones
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
        
        # Tipos de incrementos y deducciones
        self.increment_type, _ = Types.objects.get_or_create(
            id_types=100,
            defaults={
                "name": "Horas extras",
                "description": "Horas extras",
                "id_types_categories": cat_19,
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        self.deduction_type, _ = Types.objects.get_or_create(
            id_types=101,
            defaults={
                "name": "Seguridad social",
                "description": "Deducción por seguridad social",
                "id_types_categories": cat_18,
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
    
    def _create_employee(self, user_id: int, email: str, employee_status: Statues = None,
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
    
    def _create_contract(self, employee: Employee, contract_code: str,
                        charge: EmployeeCharge = None, start_date: date = None,
                        end_date: date = None, contract_status: Statues = None,
                        salary_base: float = 1000000.0) -> EmployeeContract:
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
    
    def _create_payroll(self, employee: Employee, contract: EmployeeContract,
                       start_date: date, end_date: date,
                       base_salary: float = 1000000.0) -> Payroll:
        """Crea una nómina de prueba"""
        payroll = Payroll.objects.create(
            id_employee=employee,
            id_employee_contract=contract,
            start_date=start_date,
            end_date=end_date,
            base_salary=base_salary,
            time_worked=30.0,
            total_increments=0.0,
            total_deductions=0.0,
            net_pay=base_salary,
            currency_type=self.currency,
            creation_date=self.now,
            id_responsible_user=self.user
        )
        return payroll
    
    def _create_payroll_increase(self, payroll: Payroll, amount_value: float = 100000.0) -> PayrollIncrease:
        """Crea un incremento de nómina"""
        increase = PayrollIncrease.objects.create(
            payroll=payroll,
            increase_type=self.increment_type,
            amount_type="fijo",
            application_increase_type="SalarioBase",
            amount_value=amount_value,
            amount=1.0,
            calculated_amount=amount_value,
            start_date_increase=payroll.start_date,
            end_date_increase=payroll.end_date,
            description="Incremento de prueba",
            creation_date=self.now,
            id_responsible_user=self.user
        )
        # Actualizar total de incrementos en payroll
        payroll.total_increments += increase.calculated_amount
        payroll.net_pay += increase.calculated_amount
        payroll.save()
        return increase
    
    def _create_payroll_deduction(self, payroll: Payroll, amount_value: float = 50000.0) -> PayrollDeduction:
        """Crea una deducción de nómina"""
        deduction = PayrollDeduction.objects.create(
            payroll=payroll,
            deduction_type=self.deduction_type,
            amount_type="fijo",
            application_deduction_type="SalarioBase",
            amount_value=amount_value,
            amount=1.0,
            calculated_amount=amount_value,
            start_date_deduction=payroll.start_date,
            end_date_deductions=payroll.end_date,
            description="Deducción de prueba",
            creation_date=self.now,
            id_responsible_user=self.user
        )
        # Actualizar total de deducciones en payroll
        payroll.total_deductions += deduction.calculated_amount
        payroll.net_pay -= deduction.calculated_amount
        payroll.save()
        return deduction
    
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
    
    def test_ut_nov_004_01_successful_pdf_generation(self):
        """
        UT-NOV-004-01: Generar PDF exitoso con historial de nóminas
        
        Verifica que el endpoint construye y devuelve correctamente el PDF detallado
        de nóminas para un empleado válido y rango de fechas válido.
        """
        # Arrange: Crear empleado con nóminas
        self._authenticate_client()
        
        emp1 = self._create_employee(101, "test@example.com")
        
        # Agregar mock de usuario externo by-document
        self._add_mock_user_by_document(
            "285429340", 101, "Juan", "Pérez", "García"
        )
        
        # Crear contrato
        contract = self._create_contract(
            emp1, "CON-2025-001",
            start_date=date(2025, 10, 1),
            salary_base=1000000.0
        )
        
        # Crear nóminas en el rango (sin incrementos/deducciones por cambios del modelo)
        payroll1 = self._create_payroll(
            emp1, contract,
            start_date=date(2025, 10, 1),
            end_date=date(2025, 10, 31),
            base_salary=1000000.0
        )
        
        payroll2 = self._create_payroll(
            emp1, contract,
            start_date=date(2025, 11, 1),
            end_date=date(2025, 11, 30),
            base_salary=1000000.0
        )
        
        # Act: Solicitar generación de PDF
        response = self.client.post(
            self.generate_report_endpoint,
            {
                "employeeIdentification": "285429340",
                "dateFrom": "2025-10-01",
                "dateTo": "2025-11-30",
                "reportType": "PAYROLL_HISTORY"
            },
            format='json'
        )
        
        # Assert: PDF generado correctamente
        assert response.status_code == status.HTTP_200_OK, \
            f"Expected 200, got {response.status_code}"
        
        # Verificar headers del PDF
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['Content-Disposition']
        assert 'Informe_Nomina' in response['Content-Disposition']
        
        # Verificar que el contenido existe y no está vacío
        assert response.content is not None
        assert len(response.content) > 0
        
        # El PDF debe contener bytes válidos
        assert response.content[:4] == b'%PDF'  # Signature de PDF
    
    def test_ut_nov_004_02_employee_not_found(self):
        """
        UT-NOV-004-02: Empleado no existe (documento inválido)
        
        Valida que si el documento del empleado no existe, el endpoint retorna
        mensaje claro y no genera PDF.
        """
        # Arrange: Usuario autorizado, pero documento no existe
        self._authenticate_client()
        
        # NO agregar mock de usuario -> documento no encontrado
        
        # Act: Solicitar generación con documento inexistente
        response = self.client.post(
            self.generate_report_endpoint,
            {
                "employeeIdentification": "000000000",
                "dateFrom": "2025-10-01",
                "dateTo": "2025-11-30",
                "reportType": "PAYROLL_HISTORY"
            },
            format='json'
        )
        
        # Assert: Error 404
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        data = response.json()
        assert data["success"] is False
        assert "documento" in data["message"].lower() or "registrado" in data["message"].lower()
    
    def test_ut_nov_004_03_date_range_validation(self):
        """
        UT-NOV-004-03: Validación de rango de fechas obligatorio y válido
        
        Prueba que las fechas "Desde" y "Hasta" sean obligatorias y que
        "Desde" <= "Hasta".
        """
        # Arrange
        self._authenticate_client()
        
        # Caso 1: dateFrom faltante
        response1 = self.client.post(
            self.generate_report_endpoint,
            {
                "employeeIdentification": "285429340",
                "dateTo": "2025-11-30",
                "reportType": "PAYROLL_HISTORY"
            },
            format='json'
        )
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        data1 = response1.json()
        assert "dateFrom" in str(data1.get("errors", {})) or "fecha" in data1.get("message", "").lower()
        
        # Caso 2: dateTo faltante
        response2 = self.client.post(
            self.generate_report_endpoint,
            {
                "employeeIdentification": "285429340",
                "dateFrom": "2025-10-01",
                "reportType": "PAYROLL_HISTORY"
            },
            format='json'
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        data2 = response2.json()
        assert "dateTo" in str(data2.get("errors", {})) or "fecha" in data2.get("message", "").lower()
        
        # Caso 3: dateFrom > dateTo (rango inválido)
        response3 = self.client.post(
            self.generate_report_endpoint,
            {
                "employeeIdentification": "285429340",
                "dateFrom": "2025-12-01",
                "dateTo": "2025-10-01",  # Anterior a dateFrom
                "reportType": "PAYROLL_HISTORY"
            },
            format='json'
        )
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        data3 = response3.json()
        assert "errors" in data3 or "fecha" in data3.get("message", "").lower()
    
    @pytest.mark.skip(reason="UT-NOV-004-04 es validación de frontend (botón deshabilitado), no aplica para tests de backend")
    def test_ut_nov_004_04_frontend_validation(self):
        """
        UT-NOV-004-04: Botón de descarga sólo habilitado con datos completos
        
        SKIPPED: Esta prueba se refiere a validación del frontend (deshabilitar botón).
        No es aplicable para pruebas unitarias de backend.
        """
        pass
    
    def test_ut_nov_004_05_empty_report(self):
        """
        UT-NOV-004-05: Informe vacío si no hay nóminas en rango
        
        Responde PDF con información del empleado pero sin nóminas si no existen
        registros en el rango seleccionado.
        """
        # Arrange: Empleado existe pero sin nóminas en el rango
        self._authenticate_client()
        
        emp1 = self._create_employee(501, "test@example.com")
        
        # Agregar mock de usuario externo
        self._add_mock_user_by_document(
            "111111111", 501, "Pedro", "González", "López"
        )
        
        # Crear contrato pero NO crear nóminas
        contract = self._create_contract(
            emp1, "CON-2025-501",
            start_date=date(2025, 10, 1)
        )
        
        # Act: Solicitar PDF en rango sin nóminas
        response = self.client.post(
            self.generate_report_endpoint,
            {
                "employeeIdentification": "111111111",
                "dateFrom": "2025-10-01",
                "dateTo": "2025-12-31",
                "reportType": "PAYROLL_HISTORY"
            },
            format='json'
        )
        
        # Assert: PDF generado (aunque vacío)
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar headers del PDF
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['Content-Disposition']
        
        # El PDF debe existir (aunque sin nóminas)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.content[:4] == b'%PDF'
    
    def test_ut_nov_004_06_permission_validation(self):
        """
        UT-NOV-004-06: Validación de permisos/Authentication
        
        Usuario sin token válido o permiso 194 no puede acceder ni generar el informe.
        """
        # Caso 1: Usuario sin permiso 194
        self._authenticate_client(permissions=self.token_without_permission)
        
        response1 = self.client.post(
            self.generate_report_endpoint,
            {
                "employeeIdentification": "285429340",
                "dateFrom": "2025-10-01",
                "dateTo": "2025-11-30",
                "reportType": "PAYROLL_HISTORY"
            },
            format='json'
        )
        
        assert response1.status_code == status.HTTP_403_FORBIDDEN
        data1 = response1.json()
        assert "permiso" in data1["message"].lower()
        
        # Caso 2: Sin autenticación
        client_no_auth = APIClient()
        response2 = client_no_auth.post(
            self.generate_report_endpoint,
            {
                "employeeIdentification": "285429340",
                "dateFrom": "2025-10-01",
                "dateTo": "2025-11-30",
                "reportType": "PAYROLL_HISTORY"
            },
            format='json'
        )
        
        assert response2.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        data2 = response2.json()
        assert "message" in data2
