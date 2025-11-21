"""
UT-CON-006: Pruebas para validar la actualización de deducciones en contratos preestablecidos
ID: UT-CON-006
HU: HU-CON-005 - Actualizar Contrato Preestablecido (Enfoque en Deducciones)
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
class TestEstablishedContractDeductionsUpdate:
    """Pruebas de validación para actualización de deducciones en contratos preestablecidos"""
    
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
            "id": 1,
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
        cat_18, _ = TypesCategory.objects.get_or_create(
            id_types_categories=18, 
            defaults={
                "name": "Deduction Types", 
                "description": "Deduction Types", 
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
        
        self.deduction_type_28, _ = Types.objects.get_or_create(
            id_types=28,
            defaults={
                "name": "Salud", 
                "description": "Salud", 
                "id_types_categories": cat_18, 
                "id_statues": self.status_active, 
                "creation_date": self.now, 
                "modification_date": self.now,
                "id_responsible_user": self.user
            }
        )
        
        self.deduction_type_29, _ = Types.objects.get_or_create(
            id_types=29,
            defaults={
                "name": "Pensión", 
                "description": "Pensión", 
                "id_types_categories": cat_18, 
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
        days_data = [
            (1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'),
            (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado'), (7, 'Domingo')
        ]
        for day_id, day_name in days_data:
            DaysOfWeek.objects.get_or_create(
                id_day_of_week=day_id,
                defaults={'name': day_name}
            )
    
    def _setup_base_contract(self):
        """Crear contrato base para actualizaciones"""
        # Crear contrato base
        self.base_contract = EstablishedContract.objects.create(
            contract_code='CON-ENCARGADODEVENTAS-0012',
            start_date=self.today,
            end_date=self.today + timedelta(days=14),
            salary_base=2500000,
            contract_type=self.contract_type,
            workday_type=self.workday_type,
            work_mode_type=self.modality_type,
            currency_type=self.currency,
            id_responsible_user=self.user,
            established_contract_status=self.status_active,
            id_employee_charge=self.employee_charge,
            payment_frequency_type='quincenal',
            salary_type='Mensual fijo',
            vacation_days=15,
            cumulative_vacation=True,
            start_cumulative_vacation=self.today,
            maximum_disability_days=30,
            overtime=1.25,
            creation_date=self.now,
            modification_date=self.now
        )
        
        # Crear deducción existente
        self.existing_deduction = EstablishedDeduction.objects.create(
            established_contracts_contract_code=self.base_contract,
            deduction_type=self.deduction_type_28,
            amount_type='fijo',
            amount_value=100000,
            application_deduction_type='SalarioFinal',
            start_date_deduction=self.today,
            end_date_deductions=self.today + timedelta(days=7),
            description='Deducción existente',
            amount=1
        )
        
        # Crear pagos quincenales básicos
        ContractPaymentsEstablishedContract.objects.create(
            established_contracts_contract_code=self.base_contract,
            date_payment=15
        )
        ContractPaymentsEstablishedContract.objects.create(
            established_contracts_contract_code=self.base_contract,
            date_payment=30
        )
    
    def _get_base_contract_payload(self):
        """Generar payload base válido para actualización"""
        return {
            "start_date": str(self.today),
            "end_date": str(self.today + timedelta(days=14)),
            "salary_base": 2500000,
            "contract_type": self.contract_type.id_types,
            "workday_type": self.workday_type.id_types,
            "work_mode_type": self.modality_type.id_types,
            "currency_type": self.currency.id_units,
            "payment_frequency_type": "quincenal",
            "salary_type": "Mensual fijo",
            "vacation_days": 15,
            "cumulative_vacation": True,
            "start_cumulative_vacation": str(self.today),
            "maximum_disability_days": 30,
            "overtime": 1.25,
            "contract_payments": [
                {
                    "date_payment": 15
                },
                {
                    "date_payment": 30
                }
            ],
            "established_deductions": [],
            "established_increases": []
        }
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_1_successful_deduction_update(self, mock_jwt_decode):
        """
        UT-CON-007.1 – 200 OK – Actualización exitosa de deducción (camino feliz)
        
        Verificar que el endpoint permita actualizar correctamente una deducción existente
        asociada al contrato CON-ENCARGADODEVENTAS-0012, modificando valor, fechas,
        aplicación y descripción, cumpliendo todas las validaciones.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_28.id_types,
                "amount_type": "Porcentaje",
                "amount_value": 15,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=10)),
                "description": "Deducción actualizada exitosamente",
                "amount": 2
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        if response.status_code != status.HTTP_200_OK:
            print(f"Error response: {response.json()}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['success'] is True
        assert 'actualizado exitosamente' in data['message'].lower()
        assert data['contract_code'] == 'CON-ENCARGADODEVENTAS-0012'
        
        # Verificar en base de datos
        updated_contract = EstablishedContract.objects.get(contract_code='CON-ENCARGADODEVENTAS-0012')
        deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=updated_contract
        )
        
        assert deductions.count() == 1
        deduction = deductions.first()
        assert deduction.deduction_type.id_types == self.deduction_type_28.id_types
        assert deduction.amount_type == "Porcentaje"
        assert deduction.amount_value == 15
        assert deduction.application_deduction_type == "SalarioBase"
        assert deduction.description == "Deducción actualizada exitosamente"
        assert deduction.amount == 2
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_2_missing_required_fields(self, mock_jwt_decode):
        """
        UT-CON-007.2 – 400 Bad Request – Campos obligatorios de deducción faltantes
        
        Verificar que cuando se envía un objeto en established_deductions se exijan
        los campos obligatorios: deduction_type, amount_type, amount_value, application_deduction_type.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "description": "deducción sin campos obligatorios"
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] is False
        assert 'errors' in data
        
        deduction_errors = data['errors']['established_deductions'][0]
        assert 'deduction_type' in deduction_errors
        assert 'amount_type' in deduction_errors
        assert 'amount_value' in deduction_errors
        assert 'application_deduction_type' in deduction_errors
        
        # Verificar que no se modificó la deducción en BD
        deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert deductions.count() == 1
        assert deductions.first().description == 'Deducción existente'
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_3_percentage_over_100(self, mock_jwt_decode):
        """
        UT-CON-007.3 – 400 Bad Request – Valor porcentual mayor a 100%
        
        Verificar que, cuando amount_type = "Porcentaje", el campo amount_value
        no pueda ser mayor a 100.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "Porcentaje",
                "amount_value": 150,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=7)),
                "description": "deducción porcentaje inválido",
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] is False
        
        deduction_errors = data['errors']['established_deductions'][0]
        assert 'amount_value' in deduction_errors
        assert 'mayor a 100' in deduction_errors['amount_value'][0].lower()
        
        # Verificar que la deducción no se actualizó
        deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert deductions.count() == 1
        assert deductions.first().amount_value == 100000  # Valor original
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_4_negative_values(self, mock_jwt_decode):
        """
        UT-CON-007.4 – 400 Bad Request – Valores negativos en deducción
        
        Verificar que amount_value y amount no acepten valores negativos.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "fijo",
                "amount_value": -1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=7)),
                "description": "deducción con valores negativos",
                "amount": -2
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] is False
        
        deduction_errors = data['errors']['established_deductions'][0]
        assert 'amount_value' in deduction_errors
        assert 'amount' in deduction_errors
        
        # Verificar que no se persisten cambios
        deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert deductions.count() == 1
        original_deduction = deductions.first()
        assert original_deduction.amount_value == 100000
        assert original_deduction.amount == 1
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_5_dates_outside_contract_range(self, mock_jwt_decode):
        """
        UT-CON-007.5 – 400 Bad Request – Fechas de deducción fuera del rango del contrato
        
        Verificar que start_date_deduction y end_date_deductions:
        - No sean anteriores al start_date del contrato
        - No sean posteriores al end_date del contrato
        - end_date_deductions sea posterior a start_date_deduction
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Subcaso 1: start_date_deduction antes del contrato
        payload1 = self._get_base_contract_payload()
        payload1["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "fijo",
                "amount_value": 1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today - timedelta(days=5)),
                "end_date_deductions": str(self.today + timedelta(days=5)),
                "description": "fecha inicio antes del contrato",
                "amount": 1
            }
        ]
        
        # Act & Assert - Subcaso 1
        response1 = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload1),
            content_type='application/json'
        )
        
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        data1 = response1.json()
        deduction_errors1 = data1['errors']['established_deductions'][0]
        assert 'start_date_deduction' in deduction_errors1
        assert 'anterior' in deduction_errors1['start_date_deduction'][0].lower()
        
        # Subcaso 2: end_date_deductions después del contrato
        payload2 = self._get_base_contract_payload()
        payload2["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "fijo",
                "amount_value": 1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=20)),
                "description": "fecha fin después del contrato",
                "amount": 1
            }
        ]
        
        # Act & Assert - Subcaso 2
        response2 = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload2),
            content_type='application/json'
        )
        
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        data2 = response2.json()
        deduction_errors2 = data2['errors']['established_deductions'][0]
        assert 'end_date_deductions' in deduction_errors2
        assert 'posterior' in deduction_errors2['end_date_deductions'][0].lower()
        
        # Subcaso 3: end_date antes que start_date
        payload3 = self._get_base_contract_payload()
        payload3["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "fijo",
                "amount_value": 1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=7)),
                "end_date_deductions": str(self.today + timedelta(days=3)),
                "description": "fechas incoherentes",
                "amount": 1
            }
        ]
        
        # Act & Assert - Subcaso 3
        response3 = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload3),
            content_type='application/json'
        )
        
        assert response3.status_code == status.HTTP_400_BAD_REQUEST
        data3 = response3.json()
        deduction_errors3 = data3['errors']['established_deductions'][0]
        assert 'end_date_deductions' in deduction_errors3
        assert 'posterior' in deduction_errors3['end_date_deductions'][0].lower()
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_6_description_max_length(self, mock_jwt_decode):
        """
        UT-CON-007.6 – 400 Bad Request – Descripción supera longitud máxima
        
        Verificar que el campo description de una deducción no acepte más de 255 caracteres.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Generar descripción de más de 255 caracteres
        long_description = "A" * 256
        
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "fijo",
                "amount_value": 1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=7)),
                "description": long_description,
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] is False
        
        # Verificar error de longitud
        deduction_errors = data['errors']['established_deductions'][0]
        assert 'description' in deduction_errors
        error_message = deduction_errors['description'][0].lower()
        assert '255' in error_message or 'characters' in error_message or 'caracteres' in error_message
        
        # Verificar que no se guarda la actualización
        deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert deductions.count() == 1
        assert deductions.first().description == 'Deducción existente'
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_7_duplicate_deduction_type(self, mock_jwt_decode):
        """
        UT-CON-007.7 – 400 Bad Request – Deducción duplicada por tipo y aplicación
        
        Verificar que no se puedan registrar dos deducciones con el mismo deduction_type
        y application_deduction_type para un mismo contrato.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "fijo",
                "amount_value": 1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=7)),
                "description": "Primera deducción",
                "amount": 1
            },
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "Porcentaje",
                "amount_value": 5,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=2)),
                "end_date_deductions": str(self.today + timedelta(days=8)),
                "description": "Segunda deducción duplicada",
                "amount": 2
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] is False
        
        # Verificar error de duplicidad
        error_message = str(data['errors']).lower()
        assert 'duplicada' in error_message or 'mismo tipo' in error_message or str(self.deduction_type_29.id_types) in error_message
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_8_invalid_deduction_type(self, mock_jwt_decode):
        """
        UT-CON-007.8 – 400 Bad Request – Tipo de deducción inexistente o inválido
        
        Verificar que deduction_type de cada deducción:
        - Exista en la tabla de tipos
        - Pertenezca a la categoría 18 (tipos de deducción)
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": 999,  # ID inexistente
                "amount_type": "fijo",
                "amount_value": 1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=7)),
                "description": "tipo de deducción inválido",
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert data['success'] is False
        
        deduction_errors = data['errors']['established_deductions'][0]
        assert 'deduction_type' in deduction_errors
        error_message = deduction_errors['deduction_type'][0].lower()
        assert 'no existe' in error_message or 'does not exist' in error_message
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_9_inactive_contract_modification(self, mock_jwt_decode):
        """
        UT-CON-007.9 – 403 Forbidden – Intentar modificar deducciones de contrato inactivo/finalizado
        
        Verificar que el endpoint no permita actualizar deducciones cuando el contrato
        está en estado Inactivo o Finalizado.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Cambiar contrato a inactivo
        self.base_contract.established_contract_status = self.status_inactive
        self.base_contract.save()
        
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "fijo",
                "amount_value": 1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=7)),
                "description": "intento de modificación en contrato inactivo",
                "amount": 1
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        # Nota: Según el diseño actual, el endpoint puede devolver 400 o 403
        # Verificamos que sea un error de cliente (4xx)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
        
        data = response.json()
        assert data['success'] is False
        
        # Verificar que no se modificó ninguna deducción en BD
        deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert deductions.count() == 1
        assert deductions.first().description == 'Deducción existente'
        
        # Restaurar estado activo para otras pruebas
        self.base_contract.established_contract_status = self.status_active
        self.base_contract.save()
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_10_security_restrictions(self, mock_jwt_decode):
        """
        UT-CON-007.10 – 401 / 403 – Restricciones de seguridad para deducciones
        
        Verificar que solo usuarios con permisos de modificación pueden editar o eliminar deducciones.
        """
        # Subcaso A: Sin token
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "fijo",
                "amount_value": 1000,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=7)),
                "description": "intento sin autenticación",
                "amount": 1
            }
        ]
        
        # Act & Assert - Sin token
        response_no_token = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response_no_token.status_code == status.HTTP_401_UNAUTHORIZED
        
        data_no_token = response_no_token.json()
        assert 'detail' in data_no_token or 'message' in data_no_token
        error_message = data_no_token.get('detail', data_no_token.get('message', ''))
        assert 'autenticado' in error_message.lower() or 'authentication' in error_message.lower()
        
        # Subcaso B: Usuario sin permiso 176
        mock_jwt_decode.return_value = self.token_without_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Act & Assert - Sin permiso
        response_no_permission = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response_no_permission.status_code == status.HTTP_403_FORBIDDEN
        
        data_no_permission = response_no_permission.json()
        assert 'message' in data_no_permission
        assert 'permiso' in data_no_permission['message'].lower()
        
        # Verificar que no se tocó la BD en ningún caso
        deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert deductions.count() == 1
        assert deductions.first().description == 'Deducción existente'
    
    @patch('users.authentication.jwt.decode')
    def test_ut_con_007_11_remove_deduction_successfully(self, mock_jwt_decode):
        """
        UT-CON-007.11 – 200 OK – Eliminar deducción correctamente desde el payload
        
        Simular la acción de "Eliminar deducción" desde frontend, removiendo una deducción
        del array established_deductions y verificando que se elimine del contrato.
        """
        # Arrange
        mock_jwt_decode.return_value = self.token_with_permission
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        
        # Crear una segunda deducción para tener múltiples
        second_deduction = EstablishedDeduction.objects.create(
            established_contracts_contract_code=self.base_contract,
            deduction_type=self.deduction_type_29,
            amount_type='Porcentaje',
            amount_value=5,
            application_deduction_type='SalarioBase',
            start_date_deduction=self.today + timedelta(days=1),
            end_date_deductions=self.today + timedelta(days=8),
            description='Segunda deducción a mantener',
            amount=2
        )
        
        # Verificar que tenemos 2 deducciones inicialmente
        initial_deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert initial_deductions.count() == 2
        
        # Payload que solo incluye la segunda deducción (eliminando la primera)
        payload = self._get_base_contract_payload()
        payload["established_deductions"] = [
            {
                "deduction_type": self.deduction_type_29.id_types,
                "amount_type": "Porcentaje",
                "amount_value": 5,
                "application_deduction_type": "SalarioBase",
                "start_date_deduction": str(self.today + timedelta(days=1)),
                "end_date_deductions": str(self.today + timedelta(days=8)),
                "description": "Segunda deducción a mantener",
                "amount": 2
            }
        ]
        
        # Act
        response = self.client.put(
            f'{self.endpoint_base}/CON-ENCARGADODEVENTAS-0012/update_established_contract/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data['success'] is True
        assert 'actualizado exitosamente' in data['message'].lower()
        
        # Verificar que solo queda una deducción en BD
        remaining_deductions = EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract
        )
        assert remaining_deductions.count() == 1
        
        # Verificar que es la deducción correcta
        remaining_deduction = remaining_deductions.first()
        assert remaining_deduction.deduction_type.id_types == self.deduction_type_29.id_types
        assert remaining_deduction.description == "Segunda deducción a mantener"
        assert remaining_deduction.amount_type == "Porcentaje"
        assert remaining_deduction.amount_value == 5
        
        # Verificar que la primera deducción ya no existe
        assert not EstablishedDeduction.objects.filter(
            established_contracts_contract_code=self.base_contract,
            description='Deducción existente'
        ).exists()
