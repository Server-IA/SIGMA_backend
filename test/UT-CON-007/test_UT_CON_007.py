"""
UT-CON-007: Pruebas para validar la actualización de incrementos en contratos preestablecidos
ID: UT-CON-007
HU: HU-CON-005 - Actualizar Contrato Preestablecido (Enfoque en Incrementos)
Endpoint: PUT /established_contracts/{contract_code}/update_established_contract/
Permiso: 176 (established_contract.update)
"""

import pytest
import json
from datetime import timedelta, date
from unittest.mock import patch, MagicMock
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
import jwt

from users.models import User
from parameterization.models import (
    TypesCategory, Types, UnitsCategory, Units, EmployeeCharge, 
    EmployeeDepartment, Statues, StatuesCategory
)
from payroll.models import (
    EstablishedContract, EstablishedDeduction, EstablishedIncrease,
    ContractPaymentsEstablishedContract, DaysOfWeek
)


@pytest.mark.django_db
class TestEstablishedContractIncrementsUpdate:
    """Pruebas de validación para actualización de incrementos en contratos preestablecidos"""
    
    endpoint_base = '/established_contracts'
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        self.today = self.now.date()
        self.tomorrow = self.today + timedelta(days=1)
        self.week_later = self.today + timedelta(days=7)
        
        # Crear usuario responsable
        self.user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([176])
        self.token_without_permission = self._token_with_permissions([999])
        self.invalid_token = "invalid_token"
        
        # Crear parametrización necesaria
        self._setup_parametrization()
        
        # Crear contrato base para actualizaciones
        self._setup_base_contract()
    
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
            "id": self.user.id_user,
            "email": "test@example.com",
            "name": "Test User",
            "roles": [{"permisos": perms, "permissions": perms}],
            "permisos": perms,
            "permissions": perms,
        }
    
    def _setup_parametrization(self):
        """Crea los tipos y unidades necesarias para los tests"""
        # Categorías de estados
        status_cat, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1, 
            defaults={
                "name": "Status", 
                "description": "Status", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Estados
        self.status_active, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                "name": "Activo", 
                "description": "Activo", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.status_inactive, _ = Statues.objects.get_or_create(
            id_statues=2,
            defaults={
                "name": "Inactivo", 
                "description": "Inactivo", 
                "id_statues_categories": status_cat, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categorías de tipos
        cat_15, _ = TypesCategory.objects.get_or_create(
            id_types_categories=15, 
            defaults={
                "name": "Contract Types", 
                "description": "Contract Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        cat_16, _ = TypesCategory.objects.get_or_create(
            id_types_categories=16, 
            defaults={
                "name": "Workday Types", 
                "description": "Workday Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        cat_17, _ = TypesCategory.objects.get_or_create(
            id_types_categories=17, 
            defaults={
                "name": "Work Mode Types", 
                "description": "Work Mode Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        cat_19, _ = TypesCategory.objects.get_or_create(
            id_types_categories=19, 
            defaults={
                "name": "Increment Types", 
                "description": "Increment Types", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Tipos
        self.contract_type, _ = Types.objects.get_or_create(
            id_types=20,
            defaults={
                "name": "Indefinido", 
                "description": "Indefinido", 
                "id_types_categories": cat_15, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.workday_type, _ = Types.objects.get_or_create(
            id_types=21,
            defaults={
                "name": "Completa", 
                "description": "Completa", 
                "id_types_categories": cat_16, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.modality_type, _ = Types.objects.get_or_create(
            id_types=22,
            defaults={
                "name": "Presencial", 
                "description": "Presencial", 
                "id_types_categories": cat_17, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Tipos de incremento
        self.increment_type_31, _ = Types.objects.get_or_create(
            id_types=31,
            defaults={
                "name": "Bonificación por Desempeño", 
                "description": "Bonificación por Desempeño", 
                "id_types_categories": cat_19, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.increment_type_32, _ = Types.objects.get_or_create(
            id_types=32,
            defaults={
                "name": "Auxilio de Transporte", 
                "description": "Auxilio de Transporte", 
                "id_types_categories": cat_19, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Categoría de unidades (debe ser 10 para monedas según validación del serializer)
        units_cat, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10, 
            defaults={
                "name": "Currency", 
                "description": "Currency", 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Tipo para moneda
        currency_type, _ = Types.objects.get_or_create(
            id_types=100,
            defaults={
                "name": "Currency Type", 
                "description": "Currency Type", 
                "id_types_categories": cat_15, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Moneda
        self.currency, _ = Units.objects.get_or_create(
            id_units=17,
            defaults={
                "name": "COP", 
                "symbol": "$", 
                "id_units_categories": units_cat, 
                "id_types": currency_type, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Departamento de empleado
        self.employee_department, _ = EmployeeDepartment.objects.get_or_create(
            id_employee_department=1,
            defaults={
                "name": "Ventas", 
                "description": "Ventas", 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Cargo de empleado
        self.employee_charge, _ = EmployeeCharge.objects.get_or_create(
            id_employee_charge=1,
            defaults={
                "name": "Encargado de Ventas", 
                "description": "Encargado de Ventas", 
                "id_employee_department": self.employee_department, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        # Días de la semana
        days = [
            (1, "Lunes"), (2, "Martes"), (3, "Miércoles"), 
            (4, "Jueves"), (5, "Viernes"), (6, "Sábado"), (7, "Domingo")
        ]
        for day_id, day_name in days:
            DaysOfWeek.objects.get_or_create(
                id_day_of_week=day_id,
                defaults={"name": day_name}
            )
    
    def _setup_base_contract(self):
        """Crea el contrato base CON-ENCARGADODEVENTAS-0012 con incremento existente"""
        # Crear contrato base
        self.base_contract = EstablishedContract.objects.create(
            contract_code="CON-ENCARGADODEVENTAS-0012",
            id_employee_charge=self.employee_charge,
            description="Contrato para pruebas de incrementos",
            contract_type=self.contract_type,
            start_date=date(2025, 11, 18),
            end_date=date(2025, 12, 1),
            payment_frequency_type="quincenal",
            minimum_hours=48,
            workday_type=self.workday_type,
            work_mode_type=self.modality_type,
            salary_type="Mensual fijo",
            salary_base=2500000,
            currency_type=self.currency,
            trial_period_days=30,
            vacation_days=15,
            cumulative_vacation=True,
            start_cumulative_vacation=date(2025, 11, 18),
            vacation_frequency_days=365,
            maximum_disability_days=180,
            overtime=True,
            overtime_period="dia",
            notice_period_days=30,
            established_contract_status=self.status_active,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.user
        )
        
        # Crear pagos del contrato
        ContractPaymentsEstablishedContract.objects.create(
            established_contracts_contract_code=self.base_contract,
            date_payment=15
        )
        
        ContractPaymentsEstablishedContract.objects.create(
            established_contracts_contract_code=self.base_contract,
            date_payment=30
        )
        
        # Crear incremento existente
        self.existing_increment = EstablishedIncrease.objects.create(
            established_contracts_contract_code=self.base_contract,
            increase_type=self.increment_type_31,
            amount_type="Porcentaje",
            amount_value=5,
            application_increase_type="SalarioBase",
            start_date_increase=date(2025, 11, 19),
            end_date_increase=date(2025, 11, 28),
            description="Incremento por desempeño inicial",
            amount=1
        )
    
    def _get_base_contract_payload(self):
        """Genera payload base válido para actualización de contratos"""
        return {
            "id_employee_charge": self.employee_charge.id_employee_charge,
            "description": "Contrato para pruebas de incrementos actualizado",
            "contract_type": self.contract_type.id_types,
            "start_date": "2025-11-18",
            "end_date": "2025-12-01",
            "payment_frequency_type": "quincenal",
            "minimum_hours": 48,
            "workday_type": self.workday_type.id_types,
            "work_mode_type": self.modality_type.id_types,
            "salary_type": "Mensual fijo",
            "salary_base": 2500000,
            "currency_type": self.currency.id_units,
            "trial_period_days": 30,
            "vacation_days": 15,
            "cumulative_vacation": True,
            "start_cumulative_vacation": "2025-11-18",
            "vacation_frequency_days": 365,
            "maximum_disability_days": 180,
            "overtime": True,
            "overtime_period": "dia",
            "notice_period_days": 30,
            "contract_payments": [
                {"date_payment": 15},
                {"date_payment": 30}
            ]
        }
    
    # UT-CON-008.1 – 200 OK – Actualización exitosa de incremento
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_1_successful_increment_update(self, mock_jwt_decode):
        """Verificar actualización exitosa de incremento existente con datos válidos"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "Porcentaje",
                "amount_value": 10,
                "application_increase_type": "SalarioFinal",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-28",
                "description": "Incremento por desempeño actualizado",
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "actualizado exitosamente" in data["message"]
        assert data["contract_code"] == "CON-ENCARGADODEVENTAS-0012"
        
        # Verificar en BD
        updated_increment = EstablishedIncrease.objects.get(
            established_contracts_contract_code=self.base_contract
        )
        assert updated_increment.amount_value == 10
        assert updated_increment.application_increase_type == "SalarioFinal"
        assert updated_increment.description == "Incremento por desempeño actualizado"
    
    # UT-CON-008.2 – 400 Bad Request – Campos obligatorios faltantes
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_2_missing_required_fields(self, mock_jwt_decode):
        """Verificar error cuando faltan campos obligatorios en incrementos"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "description": "incremento sin campos obligatorios"
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "established_increases" in data["errors"]
        
        errors = data["errors"]["established_increases"][0]
        assert "increase_type" in errors
        assert "This field is required" in str(errors["increase_type"])
        assert "amount_type" in errors
        assert "This field is required" in str(errors["amount_type"])
        assert "amount_value" in errors
        assert "This field is required" in str(errors["amount_value"])
        assert "application_increase_type" in errors
        assert "This field is required" in str(errors["application_increase_type"])
    
    # UT-CON-008.3 – 400 Bad Request – Valor porcentual mayor a 100%
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_3_percentage_over_100(self, mock_jwt_decode):
        """Verificar rechazo de incremento con porcentaje superior al 100%"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "Porcentaje",
                "amount_value": 150,
                "application_increase_type": "SalarioBase",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-25",
                "description": "incremento porcentaje inválido",
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "established_increases" in data["errors"]
        
        errors = data["errors"]["established_increases"][0]
        assert "amount_value" in errors
        assert "mayor a 100 cuando el tipo es porcentaje" in str(errors["amount_value"])
    
    # UT-CON-008.4 – 400 Bad Request – Valores negativos
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_4_negative_values(self, mock_jwt_decode):
        """Verificar rechazo de incremento con valores negativos"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "fijo",
                "amount_value": -50000,
                "application_increase_type": "SalarioBase",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-25",
                "description": "incremento con valores negativos",
                "amount": -2
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "established_increases" in data["errors"]
        
        errors = data["errors"]["established_increases"][0]
        assert "amount_value" in errors or "amount" in errors
        # Verificar mensajes de validación de valores negativos
        if "amount_value" in errors:
            assert "negativo" in str(errors["amount_value"]).lower() or "greater than or equal to 0" in str(errors["amount_value"])
        if "amount" in errors:
            assert "negativo" in str(errors["amount"]).lower() or "greater than or equal to 0" in str(errors["amount"])
    
    # UT-CON-008.5 – 400 Bad Request – Fechas fuera del rango del contrato
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_5_dates_outside_contract_range(self, mock_jwt_decode):
        """Verificar rechazo de incrementos con fechas incoherentes"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Subcaso 1: Fecha inicio antes del contrato
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_increase_type": "SalarioBase",
                "start_date_increase": "2025-11-10",  # Antes del contrato (2025-11-18)
                "end_date_increase": "2025-11-25",
                "description": "fecha inicio antes del contrato",
                "amount": 1
            }
        ]
        
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Subcaso 2: Fecha fin después del contrato
        payload["established_increases"][0]["start_date_increase"] = "2025-11-19"
        payload["established_increases"][0]["end_date_increase"] = "2025-12-10"  # Después del contrato (2025-12-01)
        
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Subcaso 3: Fecha fin antes que fecha inicio
        payload["established_increases"][0]["start_date_increase"] = "2025-11-25"
        payload["established_increases"][0]["end_date_increase"] = "2025-11-20"  # Antes que inicio
        
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "established_increases" in data["errors"]
        errors = data["errors"]["established_increases"][0]
        assert "end_date_increase" in errors
        assert "posterior a la fecha de inicio" in str(errors["end_date_increase"])
    
    # UT-CON-008.6 – 400 Bad Request – Descripción supera longitud máxima
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_6_description_max_length(self, mock_jwt_decode):
        """Verificar rechazo de descripción con más de 255 caracteres"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange
        long_description = "x" * 256  # 256 caracteres
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_increase_type": "SalarioBase",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-25",
                "description": long_description,
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "established_increases" in data["errors"]
        errors = data["errors"]["established_increases"][0]
        assert "description" in errors
        assert "255" in str(errors["description"]) or "characters" in str(errors["description"])
    
    # UT-CON-008.7 – 400 Bad Request – Incremento duplicado por tipo
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_7_duplicate_increment_type(self, mock_jwt_decode):
        """Verificar rechazo de incrementos duplicados por tipo"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_increase_type": "SalarioBase",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-25",
                "description": "primer incremento tipo 31",
                "amount": 1
            },
            {
                "increase_type": 31,  # Mismo tipo
                "amount_type": "Porcentaje",
                "amount_value": 10,
                "application_increase_type": "SalarioFinal",
                "start_date_increase": "2025-11-20",
                "end_date_increase": "2025-11-26",
                "description": "segundo incremento tipo 31",
                "amount": 2
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "established_increases" in data["errors"]
        error_message = str(data["errors"]["established_increases"])
        assert "No puede haber dos incrementos con el mismo tipo: 31" in error_message
    
    # UT-CON-008.8 – 400 Bad Request – Tipo de incremento inexistente
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_8_invalid_increment_type(self, mock_jwt_decode):
        """Verificar rechazo de tipo de incremento inexistente"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 999,  # ID inexistente
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_increase_type": "SalarioBase",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-25",
                "description": "tipo de incremento inválido",
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "established_increases" in data["errors"]
        errors = data["errors"]["established_increases"][0]
        assert "increase_type" in errors
        assert "no existe" in str(errors["increase_type"]) or "does not exist" in str(errors["increase_type"])
    
    # UT-CON-008.9 – 400/403 – Modificar incrementos de contrato inactivo
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_9_inactive_contract_modification(self, mock_jwt_decode):
        """Verificar que no se puedan modificar incrementos de contratos inactivos"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange - Cambiar estado del contrato a inactivo
        self.base_contract.established_contract_status = self.status_inactive
        self.base_contract.save()
        
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_increase_type": "SalarioBase",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-25",
                "description": "incremento en contrato inactivo",
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert - Esperamos error 400 o 403 según validación de negocio
        # Nota: Este test puede fallar si la validación no está implementada
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
        
        # Restaurar estado para otras pruebas
        self.base_contract.established_contract_status = self.status_active
        self.base_contract.save()
    
    # UT-CON-008.10 – 401/403 – Restricciones de seguridad
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_10_security_restrictions(self, mock_jwt_decode):
        """Verificar restricciones de autenticación y autorización"""
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,
                "amount_type": "fijo",
                "amount_value": 50000,
                "application_increase_type": "SalarioBase",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-25",
                "description": "incremento sin permisos",
                "amount": 1
            }
        ]
        
        # Subcaso A: Sin token
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert 'detail' in data or 'message' in data
        error_message = data.get('detail', data.get('message', ''))
        assert 'autenticado' in error_message.lower() or 'authentication' in error_message.lower() or 'credentials' in error_message.lower()
        
        # Subcaso B: Usuario sin permiso 176
        mock_jwt_decode.return_value = self.token_without_permission
        
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert 'message' in data
        assert 'permisos' in data['message'].lower() or 'permission' in data['message'].lower()
    
    # UT-CON-008.11 – 200 OK – Eliminación de incremento mediante payload
    @patch('users.authentication.jwt.decode')
    def test_ut_con_008_11_increment_removal(self, mock_jwt_decode):
        """Verificar eliminación de incremento mediante actualización del array"""
        mock_jwt_decode.return_value = self.token_with_permission
        
        # Arrange - Crear segundo incremento
        second_increment = EstablishedIncrease.objects.create(
            established_contracts_contract_code=self.base_contract,
            increase_type=self.increment_type_32,
            amount_type="fijo",
            amount_value=100000,
            application_increase_type="SalarioBase",
            start_date_increase=date(2025, 11, 20),
            end_date_increase=date(2025, 11, 27),
            description="Auxilio de transporte",
            amount=2
        )
        
        # Verificar que existen 2 incrementos
        assert EstablishedIncrease.objects.filter(
            established_contracts_contract_code=self.base_contract
        ).count() == 2
        
        # Act - Enviar payload con solo un incremento (eliminando el segundo)
        payload = self._get_base_contract_payload()
        payload["established_increases"] = [
            {
                "increase_type": 31,  # Solo mantener el tipo 31
                "amount_type": "Porcentaje",
                "amount_value": 8,
                "application_increase_type": "SalarioFinal",
                "start_date_increase": "2025-11-19",
                "end_date_increase": "2025-11-28",
                "description": "Incremento por desempeño mantenido",
                "amount": 1
            }
        ]
        
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer valid_token'
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        
        # Verificar en BD - Solo debe quedar 1 incremento
        remaining_increments = EstablishedIncrease.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert remaining_increments.count() == 1
        
        # Verificar que el incremento restante es el correcto
        remaining_increment = remaining_increments.first()
        assert remaining_increment.increase_type.id_types == 31
        assert remaining_increment.amount_value == 8
        assert remaining_increment.description == "Incremento por desempeño mantenido"
        
        # Verificar que el incremento tipo 32 fue eliminado
        assert not EstablishedIncrease.objects.filter(
            established_contracts_contract_code=self.base_contract,
            increase_type=self.increment_type_32
        ).exists()
