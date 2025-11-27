"""
UT-NOM-007: Pruebas unitarias para endpoint de descarga de nómina en PDF
Endpoint: GET /payroll/{id_payroll}/download/
Permiso requerido: 191 - payroll.download
"""

import pytest
import re
from datetime import datetime, date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import Mock, patch, MagicMock

from users.models import User
from parameterization.models import (
    EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory,
    TypesCategory, Types, UnitsCategory, Units
)
from payroll.models import (
    Employee, EmployeeContract, Payroll,
    PayrollIncrease, PayrollDeduction,
    EmployeeContractDeduction, EmployeeContractIncrease
)


@pytest.mark.django_db
class TestPayrollDownload:
    """Pruebas para el endpoint de descarga de nómina en PDF"""
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con permisos
        self.token_with_permission = self._token_with_permissions([191])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Patches para mocks
        self.pdf_generator_patcher = patch('payroll.api.payroll_viewset.PayrollDocumentGenerator.generate_pdf')
        self.mock_generate_pdf = self.pdf_generator_patcher.start()
        self.mock_generate_pdf.return_value = b'%PDF-1.4 Mock PDF Content'
        
        self.users_info_patcher = patch('payroll.api.payroll_viewset.get_users_info_batch')
        self.mock_get_users_info = self.users_info_patcher.start()
        self.mock_get_users_info.return_value = {}
        
        self.user_display_patcher = patch('payroll.api.payroll_viewset.get_user_display_name')
        self.mock_get_user_display = self.user_display_patcher.start()
        self.mock_get_user_display.return_value = "Test User"
        
        self.actor_info_patcher = patch('payroll.api.payroll_viewset.get_actor_info')
        self.mock_get_actor_info = self.actor_info_patcher.start()
        self.mock_get_actor_info.return_value = ("1", "Test User", "Admin")

    def teardown_method(self):
        """Limpieza después de cada prueba"""
        self.pdf_generator_patcher.stop()
        self.users_info_patcher.stop()
        self.user_display_patcher.stop()
        self.actor_info_patcher.stop()
    
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
        cat_18, _ = TypesCategory.objects.get_or_create(
            id_types_categories=18, 
            defaults={
                "name": "Deducciones", 
                "description": "Deducciones",
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
        cat_19, _ = TypesCategory.objects.get_or_create(
            id_types_categories=19, 
            defaults={
                "name": "Incrementos", 
                "description": "Incrementos",
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
                "description": "Seguridad social",
                "id_types_categories": cat_18, 
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        
        # Crear categoría de unidades y moneda
        cat_10_units, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10, 
            defaults={
                "name": "Currency Types", 
                "description": "Currency Types",
                "creation_date": self.now, 
                "modification_date": self.now
            }
        )
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
        
        # Crear departamento y cargo
        self.dept1, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={
                "name": "IT", 
                "description": "IT Dept",
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
        self.charge1, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=5,
            defaults={
                "name": "Dev", 
                "description": "Developer",
                "contract_prefix": "DEV",
                "id_employee_department": self.dept1, 
                "id_statues": self.status_active,
                "creation_date": self.now,
                "modification_date": self.now
            }
        )
    
    def _create_employee(self, user_id: int, email: str) -> Employee:
        """Crea un empleado de prueba"""
        user = self._ensure_user(user_id)
        employee = Employee.objects.create(
            id_user=user,
            email=email,
            id_employee_charge=self.charge1,
            employee_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        return employee
    
    def _create_contract(self, employee: Employee) -> EmployeeContract:
        """Crea un contrato de prueba"""
        contract = EmployeeContract.objects.create(
            contract_code="CON-TEST",
            id_employee_charge=self.charge1,
            id_employee_department=self.dept1,
            id_employee=employee,
            description="Contrato de prueba",
            contract_type=Types.objects.get(id_types=19),
            start_date=self.today,
            payment_frequency_type="mensual",
            minimum_hours=8,
            workday_type=Types.objects.get(id_types=22),
            work_mode_type=Types.objects.get(id_types=25),
            salary_type="Mensual fijo",
            salary_base=2000000.0,
            currency_type=self.currency,
            trial_period_days=30,
            vacation_days=15,
            vacation_frequency_days=360,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today + timedelta(days=7),
            maximum_disability_days=15,
            overtime=40.0,
            overtime_period="mes",
            notice_period_days=30,
            contract_status=self.status_active,
            secundary_petition=False,
            creation_date=self.now,
            id_responsible_user=self.user
        )
        return contract
    
    def _create_payroll(self, employee: Employee, contract: EmployeeContract) -> Payroll:
        """Crea una nómina de prueba"""
        payroll = Payroll.objects.create(
            id_employee=employee,
            id_employee_contract=contract,
            start_date=self.today,
            end_date=self.today + timedelta(days=30),
            base_salary=2000000.0,
            time_worked=30.0,
            total_increments=0.0,
            total_deductions=0.0,
            net_pay=2000000.0,
            currency_type=self.currency,
            creation_date=self.now,
            id_responsible_user=self.user
        )
        return payroll

    def _create_payroll_increase(self, payroll: Payroll, amount: float) -> PayrollIncrease:
        """Crea un incremento de nómina"""
        increase = PayrollIncrease.objects.create(
            payroll=payroll,
            increase_type=self.increment_type,
            amount_type="fijo",
            application_increase_type="SalarioBase",
            amount_value=amount,
            amount=1.0,
            calculated_amount=amount,
            start_date_increase=payroll.start_date,
            description="Test Inc"
        )
        payroll.total_increments += amount
        payroll.net_pay += amount
        payroll.save()
        return increase

    def _create_payroll_deduction(self, payroll: Payroll, amount: float) -> PayrollDeduction:
        """Crea una deducción de nómina"""
        deduction = PayrollDeduction.objects.create(
            payroll=payroll,
            deduction_type=self.deduction_type,
            amount_type="fijo",
            application_deduction_type="SalarioBase",
            amount_value=amount,
            amount=1.0,
            calculated_amount=amount,
            start_date_deduction=payroll.start_date,
            description="Test Ded"
        )
        payroll.total_deductions += amount
        payroll.net_pay -= amount
        payroll.save()
        return deduction
    
    def _authenticate_client(self, permissions=None):
        """Autentica el cliente con los permisos especificados"""
        token = permissions if permissions else self.token_with_permission
        self.client.force_authenticate(user=self.user)
        self.client.handler._force_token = token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer mock_token')

    # ==================== TESTS ====================

    def test_ut_nom_007_01_success(self):
        """UT-NOM-007-01: Descarga exitosa de PDF con datos completos"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        
        response = self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/pdf'
        assert 'attachment' in response['Content-Disposition']
        assert response.content == b'%PDF-1.4 Mock PDF Content'

    def test_ut_nom_007_02_not_found(self):
        """UT-NOM-007-02: Nómina no encontrada retorna 404"""
        self._authenticate_client()
        response = self.client.get('/payroll/99999/download/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "no encontrada" in response.json()['message']

    def test_ut_nom_007_03_unauthorized(self):
        """UT-NOM-007-03: Sin autenticación retorna 401"""
        client = APIClient()
        response = client.get('/payroll/1/download/')
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        assert "no autenticado" in response.json()['message'].lower()

    def test_ut_nom_007_04_forbidden(self):
        """UT-NOM-007-04: Sin permiso 191 retorna 403"""
        self._authenticate_client(permissions=self.token_without_permission)
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        
        response = self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "No tiene permisos" in response.json()['message']

    def test_ut_nom_007_05_pdf_structure(self):
        """UT-NOM-007-05: Estructura y contenido del PDF validados (vía Mock)"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        
        self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        # Verificar que se llamó al generador con los argumentos correctos
        args, kwargs = self.mock_generate_pdf.call_args
        assert kwargs['payroll'].id_payroll == payroll.id_payroll
        assert kwargs['contract'].contract_code == contract.contract_code
        assert kwargs['downloader_user'] == "Test User"

    def test_ut_nom_007_06_filename_timestamp(self):
        """UT-NOM-007-06: Nombre de archivo con timestamp correcto"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        
        response = self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        content_disposition = response['Content-Disposition']
        # Regex para validar formato: nomina_{id}_{YYYYMMDD_HHMMSS}.pdf
        pattern = r'filename="nomina_' + str(payroll.id_payroll) + r'_\d{8}_\d{6}\.pdf"'
        assert re.search(pattern, content_disposition)

    def test_ut_nom_007_07_accruals_included(self):
        """UT-NOM-007-07: Devengos fijos y adicionales incluidos en PDF"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        self._create_payroll_increase(payroll, 50000.0)
        
        self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        # Verificar que el generador recibió el payroll con los incrementos
        args, kwargs = self.mock_generate_pdf.call_args
        payroll_arg = kwargs['payroll']
        assert payroll_arg.total_increments == 50000.0
        # Nota: En el viewset se usa prefetch_related, así que podríamos verificar si los objetos relacionados están cargados
        # pero con el mock basta saber que el objeto payroll pasado es el correcto.

    def test_ut_nom_007_08_deductions_included(self):
        """UT-NOM-007-08: Deducciones fijas y adicionales incluidas en PDF"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        self._create_payroll_deduction(payroll, 30000.0)
        
        self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        args, kwargs = self.mock_generate_pdf.call_args
        payroll_arg = kwargs['payroll']
        assert payroll_arg.total_deductions == 30000.0

    def test_ut_nom_007_09_net_pay_calculation(self):
        """UT-NOM-007-09: Cálculo neto a pagar correcto en PDF"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        
        # Base 2M + 500k dev - 300k ded = 2.2M
        self._create_payroll_increase(payroll, 500000.0)
        self._create_payroll_deduction(payroll, 300000.0)
        
        self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        args, kwargs = self.mock_generate_pdf.call_args
        payroll_arg = kwargs['payroll']
        assert payroll_arg.net_pay == 2200000.0

    def test_ut_nom_007_10_employee_data(self):
        """UT-NOM-007-10: Datos del empleado correctamente precargados en PDF"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        
        # Configurar mock de usuario externo para devolver datos del empleado
        self.mock_get_users_info.return_value = {
            101: {"name": "Juan", "last_name": "Perez", "document": "123456"}
        }
        
        self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        args, kwargs = self.mock_generate_pdf.call_args
        assert kwargs['employee_data'] == {"name": "Juan", "last_name": "Perez", "document": "123456"}

    def test_ut_nom_007_11_footer_info(self):
        """UT-NOM-007-11: Pie de página con usuario y paginación"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        
        self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        args, kwargs = self.mock_generate_pdf.call_args
        assert kwargs['downloader_user'] == "Test User"
        # La paginación es responsabilidad interna del generador, aquí validamos que se pase el usuario

    def test_ut_nom_007_12_internal_error(self):
        """UT-NOM-007-12: Error interno 500 con manejo correcto"""
        self._authenticate_client()
        emp = self._create_employee(101, "test@example.com")
        contract = self._create_contract(emp)
        payroll = self._create_payroll(emp, contract)
        
        # Simular error en generador
        self.mock_generate_pdf.side_effect = Exception("PDF Error")
        
        response = self.client.get(f'/payroll/{payroll.id_payroll}/download/')
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error al generar el PDF" in response.json()['message']
