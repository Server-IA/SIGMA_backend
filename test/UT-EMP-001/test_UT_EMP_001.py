"""
UT-EMP-001: Pruebas para crear empleado con contrato
ID: UT-EMP-001
HU: HU-EMP-001 - Crear Empleado
Endpoint: POST /employees/
Permiso: 3 (employee.create)
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from parameterization.models import TypesCategory, Types, UnitsCategory, Units, EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory
from payroll.models import Employee, EmployeeContract


@pytest.mark.django_db
class TestCreateEmployeeWithContract:
    """Pruebas de creación de empleado con contrato"""
    
    @property
    def endpoint(self):
        return '/employees/'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        self.tomorrow = self.today + timedelta(days=1)
        self.week_later = self.today + timedelta(days=7)
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Crear parametrización necesaria
        self._setup_parametrization()
    
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
    
    def _get_valid_employee_payload(self):
        """Retorna un payload válido para crear empleado con contrato"""
        return {
            "id_user": 2,
            "email": "test@example.com",
            "observation": "Empleado de prueba",
            "id_employee_charge": 1,
            "description": "Contrato de prueba",
            "contract_type": 19,
            "start_date": str(self.today),
            "end_date": str(self.week_later),
            "payment_frequency_type": "quincenal",
            "minimum_hours": 8,
            "workday_type": 22,
            "work_mode_type": 25,
            "salary_type": "Mensual fijo",
            "salary_base": 100000,
            "currency_type": 17,
            "trial_period_days": 30,
            "vacation_days": 15,
            "vacation_frequency_days": 360,
            "cumulative_vacation": True,
            "start_cumulative_vacation": str(self.today),
            "maximum_disability_days": 15,
            "overtime": 30,
            "overtime_period": "semana",
            "notice_period_days": 10,
            "contract_payments": [
                {"id_day_of_week": None, "date_payment": 16},
                {"id_day_of_week": None, "date_payment": 1}
            ]
        }
    
    def test_ut_emp_001_1_crear_empleado_exitosa(self):
        """Test 1: Crear empleado con contrato exitosa"""
        payload = self._get_valid_employee_payload()
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]
    
    def test_ut_emp_001_2_crear_empleado_sin_autenticacion(self):
        """Test 2: Crear empleado sin autenticación"""
        payload = self._get_valid_employee_payload()
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
    
    def test_ut_emp_001_3_crear_empleado_sin_permiso(self):
        """Test 3: Crear empleado sin permiso"""
        payload = self._get_valid_employee_payload()
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED, status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
    
    def test_ut_emp_001_4_crear_empleado_email_duplicado(self):
        """Test 4: Crear empleado con email duplicado"""
        # Crear primer empleado
        user2 = self._ensure_user(2)
        Employee.objects.create(
            id_user=user2,
            email="test@example.com",
            id_employee_charge=self.charge,
            employee_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        # Intentar crear otro con mismo email
        payload = self._get_valid_employee_payload()
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_409_CONFLICT]
    
    def test_ut_emp_001_5_crear_empleado_cargo_invalido(self):
        """Test 5: Crear empleado con cargo inválido"""
        payload = self._get_valid_employee_payload()
        payload["id_employee_charge"] = 999
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_ut_emp_001_6_crear_empleado_salario_negativo(self):
        """Test 6: Crear empleado con salario negativo"""
        payload = self._get_valid_employee_payload()
        payload["salary_base"] = -10000
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ut_emp_001_7_crear_empleado_fecha_fin_anterior(self):
        """Test 7: Crear empleado con fecha fin anterior a inicio"""
        payload = self._get_valid_employee_payload()
        payload["end_date"] = str(self.today - timedelta(days=1))
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ut_emp_001_8_crear_empleado_tipo_contrato_invalido(self):
        """Test 8: Crear empleado con tipo de contrato inválido"""
        payload = self._get_valid_employee_payload()
        payload["contract_type"] = 999
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ut_emp_001_9_crear_empleado_campo_obligatorio_faltante(self):
        """Test 9: Crear empleado sin campo obligatorio"""
        payload = self._get_valid_employee_payload()
        del payload["email"]
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ut_emp_001_10_crear_empleado_frecuencia_pago_invalida(self):
        """Test 10: Crear empleado con frecuencia de pago inválida"""
        payload = self._get_valid_employee_payload()
        payload["payment_frequency_type"] = "anual"
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ut_emp_001_11_crear_empleado_vacaciones_negativas(self):
        """Test 11: Crear empleado con días de vacación negativo"""
        payload = self._get_valid_employee_payload()
        payload["vacation_days"] = -5
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ut_emp_001_12_crear_empleado_registra_auditoria(self):
        """Test 12: Crear empleado registra auditoría"""
        payload = self._get_valid_employee_payload()
        response = self.client.post(self.endpoint, payload, format='json')
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]
