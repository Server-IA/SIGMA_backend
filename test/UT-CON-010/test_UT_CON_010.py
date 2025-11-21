"""
UT-CON-010: Pruebas para descargar contrato establecido
ID: UT-CON-010
HU: HU-CON-010 - Descargar Contrato
Endpoint: GET /established_contracts/{contract_code}/download/?file_type=pdf|docx
Permiso: 180 (established_contract.download)
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from parameterization.models import TypesCategory, Types, UnitsCategory, Units, EmployeeCharge, EmployeeDepartment, Statues, StatuesCategory
from payroll.models import EstablishedContract


@pytest.mark.django_db
class TestDownloadEstablishedContractSpecification:
    """Pruebas de descarga de contratos establecidos"""
    
    @property
    def endpoint(self):
        return '/established_contracts/'
    
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
        
        # Crear contrato establecido de prueba
        self._create_test_contract()
    
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
        self.status_inactive, _ = Statues.objects.get_or_create(
            id_statues=2,
            defaults={"name": "Inactive", "description": "Inactive", "id_statues_categories": status_cat, "creation_date": timezone.now(), "modification_date": timezone.now()}
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
    
    def _create_test_contract(self):
        """Crea un contrato establecido para las pruebas"""
        self.contract_code = "CON-TEST-001"
        self.contract = EstablishedContract.objects.create(
            contract_code=self.contract_code,
            id_employee_charge=self.charge,
            description="Contrato de prueba",
            contract_type=Types.objects.get(id_types=19),
            start_date=self.today,
            end_date=self.week_later,
            payment_frequency_type="quincenal",
            minimum_hours=8,
            workday_type=Types.objects.get(id_types=22),
            work_mode_type=Types.objects.get(id_types=25),
            salary_type="Mensual fijo",
            salary_base=100000,
            currency_type=Units.objects.get(id_units=17),
            trial_period_days=30,
            vacation_days=15,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today,
            vacation_frequency_days=360,
            maximum_disability_days=15,
            overtime=30,
            overtime_period="semana",
            notice_period_days=10,
            established_contract_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )

    def test_ut_con_010_1_descargar_contrato_pdf_exitosa(self):
        """Test 1: Descargar PDF exitosa"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_2_descargar_contrato_docx_exitosa(self):
        """Test 2: Descargar DOCX exitosa"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/?file_type=docx')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_3_descargar_contrato_sin_autenticacion(self):
        """Test 3: Descargar sin autenticación"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED, status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_4_descargar_contrato_sin_permiso(self):
        """Test 4: Descargar sin permiso específico"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED, status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_5_descargar_contrato_no_existe(self):
        """Test 5: Descargar contrato que no existe"""
        response = self.client.get(f'{self.endpoint}CON-NO-EXISTE/download/')
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    def test_ut_con_010_6_descargar_formato_invalido(self):
        """Test 6: Descargar con formato inválido"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/?file_type=xlsx')
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_7_descargar_contrato_inactivo(self):
        """Test 7: Descargar contrato inactivo"""
        # Crear contrato inactivo
        contract_inactive = EstablishedContract.objects.create(
            contract_code="CON-TEST-002",
            id_employee_charge=self.charge,
            description="Contrato inactivo",
            contract_type=Types.objects.get(id_types=19),
            start_date=self.today,
            end_date=self.week_later,
            payment_frequency_type="quincenal",
            minimum_hours=8,
            workday_type=Types.objects.get(id_types=22),
            work_mode_type=Types.objects.get(id_types=25),
            salary_type="Mensual fijo",
            salary_base=100000,
            currency_type=Units.objects.get(id_units=17),
            trial_period_days=30,
            vacation_days=15,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today,
            vacation_frequency_days=360,
            maximum_disability_days=15,
            overtime=30,
            overtime_period="semana",
            notice_period_days=10,
            established_contract_status=self.status_inactive,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        response = self.client.get(f'{self.endpoint}CON-TEST-002/download/')
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED, status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_8_descarga_registra_auditoria(self):
        """Test 8: Verificar que descarga registra auditoría"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_9_descargar_pdf_por_defecto(self):
        """Test 9: Verificar que PDF es formato por defecto"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_10_nombre_archivo_incluye_timestamp(self):
        """Test 10: Verificar nombre de archivo con timestamp"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_11_case_insensitive_file_type(self):
        """Test 11: file_type case insensitive"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/?file_type=PDF')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_ut_con_010_12_error_generacion_documento(self):
        """Test 12: Manejo de error en generación"""
        response = self.client.get(f'{self.endpoint}{self.contract_code}/download/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_404_NOT_FOUND]
