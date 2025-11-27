"""
UT-NOM-005: Pruebas para listar nóminas generadas
ID: UT-NOM-005
HU: HU-NOM-005 - Listado de nóminas generadas
Endpoint: GET /payroll/list-generated/
Permiso: 193 (payroll.retrieve)
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from users.models import User
from parameterization.models import UnitsCategory, Units, Statues, StatuesCategory, Types, TypesCategory
from parameterization.models import EmployeeCharge, EmployeeDepartment
from payroll.models import Employee, EmployeeContract, Payroll


@pytest.mark.django_db
class TestListGeneratedPayrolls:
    """Pruebas para listado de nóminas generadas"""

    def setup_method(self):
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        self.week_later = self.today + timedelta(days=7)
        self.month_later = self.today + timedelta(days=30)

        # usuario responsable
        self.user = self._ensure_user(1)

        # parametrización mínima
        self._setup_parametrization()

        # empleado + contrato
        self._create_employee_and_contract()

        # crear varias nóminas
        self._create_payrolls(5)

    def _ensure_user(self, user_id: int) -> User:
        user, created = User.objects.get_or_create(id_user=user_id)
        user.id = user.id_user
        user.is_authenticated = True
        if created:
            user.save()
        return user

    def _setup_parametrization(self):
        sc, _ = StatuesCategory.objects.get_or_create(id_statues_categories=1, defaults={"name": "Status", "description": "Status", "creation_date": timezone.now(), "modification_date": timezone.now()})
        self.status_active, _ = Statues.objects.get_or_create(id_statues=1, defaults={"name": "Active", "description": "Active", "id_statues_categories": sc, "creation_date": timezone.now(), "modification_date": timezone.now()})

        tc1, _ = TypesCategory.objects.get_or_create(id_types_categories=15, defaults={"name": "Contract Types", "description": "Contract Types", "creation_date": timezone.now(), "modification_date": timezone.now()})
        Types.objects.get_or_create(id_types=19, defaults={"name": "Type 19", "description": "", "id_types_categories": tc1, "id_statues": self.status_active, "creation_date": timezone.now(), "modification_date": timezone.now()})

        uc, _ = UnitsCategory.objects.get_or_create(id_units_categories=10, defaults={"name": "Currency Types", "description": "Currency", "creation_date": timezone.now(), "modification_date": timezone.now()})
        Units.objects.get_or_create(id_units=99, defaults={"name": "Dollar", "symbol": "$", "id_units_categories": uc, "id_types": Types.objects.get(id_types=19), "id_statues": self.status_active})

        # departamento y cargo mínimos
        dept, _ = EmployeeDepartment.objects.get_or_create(id_employee_department=1, defaults={"name": "Dept 1", "id_statues": self.status_active, "creation_date": timezone.now(), "modification_date": timezone.now()})
        self.charge, _ = EmployeeCharge.objects.get_or_create(id_employee_charge=1, defaults={"name": "Cargo 1", "description": "Cargo test", "id_employee_department": dept, "id_statues": self.status_active, "creation_date": timezone.now(), "modification_date": timezone.now()})

    def _create_employee_and_contract(self):
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
            workday_type=Types.objects.get(id_types=19),
            work_mode_type=Types.objects.get(id_types=19),
            salary_type="Mensual fijo",
            salary_base=100000,
            currency_type=Units.objects.get(id_units=99),
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

    def _create_payrolls(self, n=5):
        currency = Units.objects.get(id_units=99)
        for i in range(n):
            Payroll.objects.create(
                id_employee=self.employee,
                id_employee_contract=self.contract,
                start_date=self.today,
                end_date=self.month_later,
                creation_date=timezone.now(),
                currency_type=currency,
                id_responsible_user=self.user
            )

    def _authenticate_with_permission(self, permission_id=193):
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
        from users.authentication import JWTAuthentication

        def _no_auth(self, request):
            return None

        JWTAuthentication.authenticate = _no_auth

    @patch('payroll.serializers.payroll_serializers.payroll_list_serializer.requests.post')
    def test_ut_nom_005_1_list_generated_success(self, mock_post):
        """Test 1: Listado exitoso con permiso 193"""
        # Mock para evitar llamadas HTTP externas
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'data': [{
                'id': 1,
                'name': 'Juan Andres',
                'first_last_name': 'Veru',
                'second_last_name': 'Sarmiento',
                'document_number': '12345678'
            }]
        }
        mock_post.return_value.content = b'{"data": []}'
        
        self._authenticate_with_permission(193)
        response = self.client.get('/payroll/list-generated/')
        
        assert response.status_code == status.HTTP_200_OK
        
        body = response.json()
        assert 'success' in body
        assert body['success'] is True
        assert 'data' in body
        
        data = body['data']
        assert isinstance(data, list)
        assert len(data) >= 5, f"Se esperaban al menos 5 nóminas, se obtuvieron {len(data)}"
        
        # Verificar estructura de cada elemento del listado
        for item in data:
            assert 'id_payroll' in item
            assert isinstance(item['id_payroll'], int)
            assert 'creation_date' in item
            assert 'start_date' in item
            assert 'end_date' in item
            assert 'currency_type_name' in item

    def test_ut_nom_005_2_list_generated_unauthenticated(self):
        """Test 2: Sin autenticación -> 401"""
        self._clear_authentication()
        endpoint = '/payroll/list-generated/'
        response = self.client.get(endpoint)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_ut_nom_005_3_list_generated_forbidden(self):
        """Test 3: Con autenticación pero sin permiso 193 -> 403"""
        self._authenticate_with_permission(999)
        endpoint = '/payroll/list-generated/'
        response = self.client.get(endpoint)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('payroll.serializers.payroll_serializers.payroll_list_serializer.requests.post')
    def test_ut_nom_005_4_fields_and_currency_name(self, mock_post):
        """Test 4: Verificar que todas las nóminas tienen currency_type_name correcto"""
        # Mock para evitar llamadas HTTP externas
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'data': []}
        mock_post.return_value.content = b'{"data": []}'
        
        self._authenticate_with_permission(193)
        response = self.client.get('/payroll/list-generated/')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()['data']
        assert isinstance(data, list)
        assert len(data) > 0, "Debe haber al menos una nómina en el listado"
        
        # Verificar que todas las nóminas tienen currency_type_name == 'Dollar'
        for item in data:
            assert item['currency_type_name'] == 'Dollar', \
                f"Nómina {item['id_payroll']} tiene currency_type_name={item['currency_type_name']}, se esperaba 'Dollar'"
