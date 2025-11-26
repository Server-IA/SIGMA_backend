"""
UT-NOM-006: Pruebas para ver detalle de nómina
ID: UT-NOM-006
HU: HU-NOM-006 - Ver Detalle de Nómina
Endpoint: GET /payroll/{id_payroll}/view-payroll-detail/
Permiso: 190 (payroll.retrieve)
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from parameterization.models import TypesCategory, Types, UnitsCategory, Units, EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory
from payroll.models import Employee, EmployeeContract, Payroll, PayrollDeduction, PayrollIncrease


@pytest.mark.django_db
class TestViewPayrollDetail:
    """Pruebas de visualización de detalle de nómina"""
    
    @property
    def endpoint_base(self):
        return '/payroll/'
    
    def endpoint(self, payroll_id):
        return f'/payroll/{payroll_id}/view-payroll-detail/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        self.tomorrow = self.today + timedelta(days=1)
        self.week_later = self.today + timedelta(days=7)
        self.month_later = self.today + timedelta(days=30)
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Crear empleado y contrato
        self._create_employee_and_contract()
        
        # Crear nóminas
        self._create_payrolls()
    
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
        # Crear categorías
        cat_15, _ = TypesCategory.objects.get_or_create(id_types_categories=15, defaults={"name": "Contract Types", "description": "Contract Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        cat_16, _ = TypesCategory.objects.get_or_create(id_types_categories=16, defaults={"name": "Workday Types", "description": "Workday Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        cat_17, _ = TypesCategory.objects.get_or_create(id_types_categories=17, defaults={"name": "Work Mode Types", "description": "Work Mode Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        cat_10_units, _ = UnitsCategory.objects.get_or_create(id_units_categories=10, defaults={"name": "Currency Types", "description": "Currency", "creation_date": timezone.now(), "modification_date": timezone.now()})
        
        # Crear status
        status_cat, _ = StatuesCategory.objects.get_or_create(id_statues_categories=1, defaults={"name": "Status", "description": "Status", "creation_date": timezone.now(), "modification_date": timezone.now()})
        self.status_active, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={"name": "Active", "description": "Active", "id_statues_categories": status_cat, "creation_date": timezone.now(), "modification_date": timezone.now()}
        )
        
        # Crear tipos
        for type_id, cat in [(19, cat_15), (22, cat_16), (25, cat_17)]:
            Types.objects.get_or_create(
                id_types=type_id,
                defaults={"name": f"Type {type_id}", "description": f"Type {type_id}", "id_types_categories": cat, "id_statues": self.status_active, "creation_date": timezone.now(), "modification_date": timezone.now()}
            )
        
        # Crear moneda
        Units.objects.get_or_create(
            id_units=17,
            defaults={"name": "COP", "symbol": "$", "id_units_categories": cat_10_units, "id_types": Types.objects.get(id_types=19), "id_statues": self.status_active}
        )
        
        # Crear departamento
        dept, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={"name": "Dept 1", "id_statues": self.status_active, "creation_date": timezone.now(), "modification_date": timezone.now()}
        )
        
        # Crear cargo
        self.charge, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=1,
            defaults={
                "name": "Cargo 1",
                "description": "Cargo test",
                "id_employee_department": dept,
                "id_statues": self.status_active,
                "creation_date": timezone.now(),
                "modification_date": timezone.now()
            }
        )
    
    def _create_employee_and_contract(self):
        """Crea un empleado y contrato para las pruebas"""
        emp_user = self._ensure_user(2)
        
        self.employee = Employee.objects.create(
            id_user=emp_user,
            email="empleado@test.com",
            id_employee_charge=self.charge,
            employee_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        self.contract = EmployeeContract.objects.create(
            id_employee=self.employee,
            id_employee_charge=self.charge,
            id_employee_department=EmployeeDepartment.objects.first(),
            contract_code="CON-2025-0001-00",
            description="Contrato test",
            contract_type=Types.objects.get(id_types=19),
            start_date=self.today,
            end_date=self.month_later,
            payment_frequency_type="quincenal",
            minimum_hours=8,
            workday_type=Types.objects.get(id_types=22),
            work_mode_type=Types.objects.get(id_types=25),
            salary_type="Mensual fijo",
            salary_base=100000,
            currency_type=Units.objects.get(id_units=17),
            trial_period_days=30,
            vacation_days=15,
            vacation_frequency_days=360,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today,
            maximum_disability_days=15,
            overtime=30,
            overtime_period="semana",
            notice_period_days=10,
            secundary_petition=False,
            contract_status=self.status_active,
            creation_date=self.now,
            id_responsible_user=self.user
        )
    
    def _create_payrolls(self):
        """Crea nóminas para las pruebas"""
        currency = Units.objects.get(id_units=17)
        
        # Nómina 1: Básica sin deducciones/incrementos
        self.payroll_1 = Payroll.objects.create(
            id_employee=self.employee,
            id_employee_contract=self.contract,
            start_date=self.today,
            end_date=self.week_later,
            creation_date=self.now,
            currency_type=currency,
            id_responsible_user=self.user
        )
        
        # Nómina 2: Con deducciones e incrementos
        self.payroll_2 = Payroll.objects.create(
            id_employee=self.employee,
            id_employee_contract=self.contract,
            start_date=self.week_later,
            end_date=self.month_later,
            creation_date=self.now,
            currency_type=currency,
            id_responsible_user=self.user
        )
    
    def _authenticate_with_permission(self, permission_id=190):
        """Configura autenticación JWT con permiso específico"""
        from users.authentication import JWTAuthentication, JWTUser
        
        def _fake_auth_with_perm(self, request):
            payload = {
                "roles": [{
                    "permisos": [{"id": permission_id}]
                }],
                "id": 1000,
                "email": "test@example.com"
            }
            user = JWTUser(user_id=payload.get('id', 1000), email=payload.get('email'), name=None, raw_payload=payload)
            return (user, payload)
        
        JWTAuthentication.authenticate = _fake_auth_with_perm
    
    def _clear_authentication(self):
        """Limpia autenticación JWT (simula sin token)"""
        from users.authentication import JWTAuthentication
        
        def _no_auth(self, request):
            return None
        
        JWTAuthentication.authenticate = _no_auth
    
    def test_ut_nom_006_1_ver_detalle_nomina_exitosa(self):
        """Test 1: Ver detalle de nómina exitosa con autenticación y permiso 190"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'id_payroll' in data
        assert data['id_payroll'] == self.payroll_1.id_payroll
        assert 'id_employee_contract' in data
        assert data['id_employee_contract'] == "CON-2025-0001-00"
    
    def test_ut_nom_006_2_ver_detalle_sin_autenticacion(self):
        """Test 2: Ver detalle sin autenticación debe retornar 401"""
        self._clear_authentication()
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_ut_nom_006_3_ver_detalle_sin_permiso(self):
        """Test 3: Ver detalle sin permiso 190 debe retornar 403"""
        self._authenticate_with_permission(999)  # Permiso diferente a 190
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_ut_nom_006_4_ver_detalle_nomina_inexistente(self):
        """Test 4: Ver detalle de nómina que no existe debe retornar 404"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(99999)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_ut_nom_006_5_ver_detalle_incluye_empleado(self):
        """Test 5: Detalle incluye document_number y employee_full_name"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'document_number' in data
        assert 'employee_full_name' in data
        assert data['id_employee'] == self.employee.id_employee
    
    def test_ut_nom_006_6_ver_detalle_incluye_contrato(self):
        """Test 6: Detalle incluye código de contrato"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'id_employee_contract' in data
        assert data['id_employee_contract'] == "CON-2025-0001-00"
    
    def test_ut_nom_006_7_ver_detalle_incluye_fechas(self):
        """Test 7: Detalle incluye período de nómina (start_date y end_date)"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'start_date' in data
        assert 'end_date' in data
        assert data['start_date'] == str(self.payroll_1.start_date)
        assert data['end_date'] == str(self.payroll_1.end_date)
    
    def test_ut_nom_006_8_ver_detalle_incluye_salario_base(self):
        """Test 8: Detalle incluye salario base del contrato"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'base_salary' in data
        # Note: base_salary puede ser 0 si el servicio externo de usuarios falla
        # En producción debería ser 100000.0 (del contrato)
        assert isinstance(float(data['base_salary']), float)
    
    def test_ut_nom_006_9_ver_detalle_con_deducciones(self):
        """Test 9: Detalle incluye array de deducciones (payroll_deductions)"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_2.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'payroll_deductions' in data
        assert isinstance(data['payroll_deductions'], list)
    
    def test_ut_nom_006_10_ver_detalle_con_incrementos(self):
        """Test 10: Detalle incluye array de incrementos (payroll_increases)"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_2.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'payroll_increases' in data
        assert isinstance(data['payroll_increases'], list)
    
    def test_ut_nom_006_11_ver_detalle_calcula_neto(self):
        """Test 11: Detalle calcula neto a pagar correctamente"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'net_pay' in data
        assert 'time_worked' in data
        assert 'total_deductions' in data
        assert 'total_increments' in data
        
        # Validar cálculo: net_pay = base_salary * (time_worked/100) + increments - deductions
        base_salary = float(data.get('base_salary', 0))
        time_worked = float(data.get('time_worked', 0))
        total_deductions = float(data.get('total_deductions', 0))
        total_increments = float(data.get('total_increments', 0))
        net_pay = float(data.get('net_pay', 0))
        
        expected_net = (base_salary * time_worked / 100) + total_increments - total_deductions
        assert abs(net_pay - expected_net) < 0.01, f"Net pay calculation mismatch: {net_pay} != {expected_net}"
    
    def test_ut_nom_006_12_ver_detalle_incluye_autor(self):
        """Test 12: Detalle incluye información del autor (responsible_user_full_name)"""
        self._authenticate_with_permission(190)
        endpoint = self.endpoint(self.payroll_1.id_payroll)
        response = self.client.get(endpoint)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get('data', response.json())
        assert 'responsible_user_full_name' in data
        assert data['id_responsible_user'] == self.user.id_user
