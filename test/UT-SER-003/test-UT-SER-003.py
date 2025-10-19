"""
Pruebas unitarias para el endpoint de actualización de servicios
ID: UT-SER-003 (HU-SER-003)
Fecha: 14/10/2025
Ejecutado por: Juan Camilo
"""

import os
import sys
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Django ya está configurado por conftest.py, solo importamos lo necesario
from django.utils import timezone as django_timezone
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from rest_framework.test import APIClient
from rest_framework import status

# Model imports
from service_requests.models.services import Service
from parameterization.models import (
    Types, TypesCategory, Units, UnitsCategory, Statues, StatuesCategory
)
from users.models.user import User


# ==============================
# Utilidades de prueba y reporte
# ==============================

class Report:
    rows = []

    @classmethod
    def add(cls, case_id, title, payload, status_code, response_json, approved):
        try:
            resp_obj = response_json if isinstance(response_json, dict) else response_json()
        except Exception:
            resp_obj = {}
        
        # Mostrar resultado en consola
        estado = '✅ APROBADO' if approved else '❌ NO APROBADO'
        print(f"\n{case_id}: {title}")
        print(f"HTTP {status_code} - {estado}")
        if not approved:
            print(f"❗ Respuesta: {resp_obj}")
        
        cls.rows.append({
            'id': case_id,
            'title': title,
            'payload': payload,
            'status_code': status_code,
            'response': resp_obj,
            'approved': approved,
        })

    @classmethod
    def generate_markdown_report(cls):
        """Genera reporte en formato Markdown"""
        total_tests = len(cls.rows)
        passed_tests = sum(1 for row in cls.rows if row['approved'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""# Reporte de Pruebas Unitarias - UT-SER-003

## Resumen Ejecutivo
- **Total de Pruebas**: {total_tests}
- **Pruebas Exitosas**: {passed_tests} ✅
- **Pruebas Fallidas**: {failed_tests} ❌
- **Tasa de Éxito**: {success_rate:.1f}%
- **Fecha de Ejecución**: {datetime.now().strftime('%d/%m/%Y')}
- **Ejecutado por**: Juan Camilo

---

"""
        
        for row in cls.rows:
            status_icon = "✅" if row['approved'] else "❌"
            report += f"""## {row['id']}

**Título**: {row['title']}

**Payload**:
```json
{json.dumps(row['payload'], indent=2, ensure_ascii=False)}
```

**Resultado Esperado**: HTTP {row['status_code']}

**Resultado Obtenido**: {status_icon} **{'PASÓ' if row['approved'] else 'FALLÓ'}** - HTTP {row['status_code']}

**Estado**: {status_icon} **{'EXITOSA' if row['approved'] else 'FALLIDA'}**

**Fecha Ejecución**: {datetime.now().strftime('%d/%m/%Y')}

**Ejecutado por**: Juan Camilo

---

"""
        
        return report


@pytest.fixture(scope='module', autouse=True)
def _write_report_on_module_end():
    Report.rows = []
    yield
    # Generar reporte al final del módulo
    report_content = Report.generate_markdown_report()
    with open('test/UT-SER-003/reporte_casodeprueba.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"\n📊 Reporte generado: test/UT-SER-003/reporte_casodeprueba.md")


@pytest.mark.django_db
class TestServiceUpdate:
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Configura datos de prueba necesarios"""
        # Crear categorías usando get_or_create para evitar duplicados
        self.service_category, _ = TypesCategory.objects.get_or_create(
            id_types_categories=14,
            defaults={
                'name': "Tipos de servicios",
                'description': "Categoría para tipos de servicios",
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now()
            }
        )
        
        self.currency_category, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10,
            defaults={
                'name': "Unidades de moneda",
                'description': "Categoría para unidades de moneda",
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now()
            }
        )
        
        self.status_category, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                'name': "Estados de servicios",
                'description': "Categoría para estados de servicios",
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now()
            }
        )
        
        # Crear estado activo primero
        self.active_status, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                'name': "Activo",
                'description': "Estado activo del servicio",
                'id_statues_categories': self.status_category,
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now()
            }
        )
        
        # Crear tipos de servicio
        self.service_type, _ = Types.objects.get_or_create(
            id_types=17,
            defaults={
                'name': "Mantenimiento Preventivo",
                'description': "Tipo de servicio de mantenimiento preventivo",
                'id_types_categories': self.service_category,
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now(),
                'id_statues': self.active_status
            }
        )
        
        # Crear unidad de precio
        self.price_unit, _ = Units.objects.get_or_create(
            id_units=17,
            defaults={
                'name': "Peso Colombiano",
                'symbol': "COP",
                'id_units_categories': self.currency_category,
                'id_types': self.service_type,
                'id_statues': self.active_status,
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now()
            }
        )
        
        # Crear usuario de prueba
        self.test_user, _ = User.objects.get_or_create(id_user=1)
        
        # Crear servicio de prueba para actualizar
        self.test_service, _ = Service.objects.get_or_create(
            id_service=1,
            defaults={
                'service_name': "Servicio Original",
                'description': "Descripción original",
                'service_type': self.service_type,
                'base_price': 100000.0,
                'price_unit': self.price_unit,
                'applicable_tax': 1,
                'tax_rate': 19.0,
                'is_vat_exempt': False,
                'service_status': self.active_status,
                'id_responsible_user': self.test_user
            }
        )
        
        # Configurar cliente API
        self.client = APIClient()
        
        # Mock de JWT con permisos
        self.jwt_payload = {
            "id": 1,
            "email": "test@example.com",
            "name": "Usuario de Prueba",
            "rol": [{
                "id": 1,
                "name": "Administrador",
                "permisos": [{"id": 141, "name": "service.update"}]
            }]
        }
        
        # Mock de autenticación
        self.auth_mock = MagicMock()
        self.auth_mock.is_authenticated = True
        self.auth_mock.id = 1
        self.auth_mock.email = "test@example.com"
        self.auth_mock.name = "Usuario de Prueba"
        self.auth_mock.roles = self.jwt_payload["rol"]
        
        # Configurar el cliente con autenticación mock
        self.client.force_authenticate(user=self.auth_mock)
    
    def test_successful_service_update(self):
        """UT-SER-003: 200 OK / 201 Created – Actualización exitosa (camino feliz)"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Mantenimiento PreventivoSOSo",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            with patch('service_requests.api.service_viewset.get_actor_info', return_value=(1, "Test User", "Admin")):
                with patch('service_requests.api.service_viewset.AuditClient'):
                    response = self.client.patch(
                        endpoint,
                        data=json.dumps(payload),
                        content_type='application/json',
                    )
        
        # Verificar respuesta
        approved = (
            response.status_code in [200, 201] and
            response.data.get('success') is True and
            response.data.get('message') == "Servicio actualizado exitosamente" and
            response.data.get('service_id') == 1
        )
        
        Report.add(
            "UT-SER-003",
            "200 OK / 201 Created – Actualización exitosa (camino feliz)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected successful update, got: {response.data}"
    
    def test_duplicate_service_name(self):
        """UT-SER-003.1: 409 Conflict – Nombre duplicado"""
        # Crear otro servicio con nombre que queremos usar
        Service.objects.get_or_create(
            id_service=2,
            defaults={
                'service_name': "Mantenimiento PreventivoSOSo",
                'description': "Otro servicio",
                'service_type': self.service_type,
                'base_price': 200000.0,
                'price_unit': self.price_unit,
                'applicable_tax': 1,
                'tax_rate': 19.0,
                'is_vat_exempt': False,
                'service_status': self.active_status,
                'id_responsible_user': self.test_user
            }
        )
        
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Mantenimiento PreventivoSOSo",
            "description": "desc",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code in [400, 409] and
            response.data.get('success') is False and
            'Ya existe un servicio con este nombre' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-003.1",
            "409 Conflict – Nombre duplicado",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected duplicate name error, got: {response.data}"
    
    def test_missing_required_fields(self):
        """UT-SER-003.2: 400 Bad Request – Campos obligatorios faltantes"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "",
            "description": "x",
            "service_type": None,
            "base_price": None,
            "price_unit": None,
            "applicable_tax": None,
            "tax_rate": None,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            (
                'service_name' in str(response.data.get('errors', {})) or
                'service_type' in str(response.data.get('errors', {})) or
                'base_price' in str(response.data.get('errors', {})) or
                'price_unit' in str(response.data.get('errors', {})) or
                'applicable_tax' in str(response.data.get('errors', {}))
            )
        )
        
        Report.add(
            "UT-SER-003.2",
            "400 Bad Request – Campos obligatorios faltantes",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for missing fields, got: {response.data}"
    
    def test_negative_base_price(self):
        """UT-SER-003.3: 400 – Precio base negativo"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Srv X",
            "description": "x",
            "service_type": 17,
            "base_price": -1.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'El precio base debe ser mayor a 0' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-003.3",
            "400 – Precio base negativo",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected negative price error, got: {response.data}"
    
    def test_zero_base_price(self):
        """UT-SER-003.4: 400 – Precio base en cero"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Srv X",
            "description": "x",
            "service_type": 17,
            "base_price": 0.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'El precio base debe ser mayor a 0' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-003.4",
            "400 – Precio base en cero",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected zero price error, got: {response.data}"
    
    def test_invalid_price_unit_category(self):
        """UT-SER-003.5: 400 – Unidad de precio fuera de categoría válida"""
        # Crear unidad de precio en categoría incorrecta
        wrong_category, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=99,
            defaults={
                'name': "Categoría Incorrecta",
                'description': "Categoría que no es de moneda",
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now()
            }
        )
        
        wrong_unit, _ = Units.objects.get_or_create(
            id_units=99,
            defaults={
                'name': "Unidad Incorrecta",
                'symbol': "INC",
                'id_units_categories': wrong_category,
                'id_types': self.service_type,
                'id_statues': self.active_status,
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now()
            }
        )
        
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Srv X",
            "description": "x",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 99,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'La unidad de precio debe pertenecer a la categoría' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-003.5",
            "400 – Unidad de precio fuera de categoría válida",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected invalid price unit category error, got: {response.data}"
    
    def test_invalid_service_type_category(self):
        """UT-SER-003.6: 400 – Tipo de servicio fuera de su categoría"""
        # Crear tipo de servicio en categoría incorrecta
        wrong_category, _ = TypesCategory.objects.get_or_create(
            id_types_categories=88,
            defaults={
                'name': "Categoría Incorrecta",
                'description': "Categoría que no es de servicios",
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now()
            }
        )
        
        wrong_type, _ = Types.objects.get_or_create(
            id_types=88,
            defaults={
                'name': "Tipo Incorrecto",
                'description': "Tipo que no pertenece a servicios",
                'id_types_categories': wrong_category,
                'creation_date': django_timezone.now(),
                'modification_date': django_timezone.now(),
                'id_statues': self.active_status
            }
        )
        
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Srv X",
            "description": "x",
            "service_type": 88,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'El tipo de servicio debe pertenecer a la categoría' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-003.6",
            "400 – Tipo de servicio fuera de su categoría",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected invalid service type category error, got: {response.data}"
    
    def test_blank_service_name(self):
        """UT-SER-003.7: 400 – Nombre vacío o solo espacios"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": " ",
            "description": "x",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            ('El nombre del servicio no puede estar vacío' in str(response.data.get('errors', {})) or
             'This field may not be blank' in str(response.data.get('errors', {})))
        )
        
        Report.add(
            "UT-SER-003.7",
            "400 – Nombre vacío o solo espacios",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected blank name error, got: {response.data}"
    
    def test_service_name_max_length(self):
        """UT-SER-003.8: 400 – Longitud máxima de nombre superada (max_length=100)"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        long_name = "A" * 101  # 101 caracteres
        payload = {
            "service_name": long_name,
            "description": "x",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'service_name' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-003.8",
            "400 – Longitud máxima de nombre superada (max_length=100)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected max length error for service name, got: {response.data}"
    
    def test_description_max_length(self):
        """UT-SER-003.9: 400 – Longitud máxima de descripción superada (max_length=500)"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        long_description = "A" * 501  # 501 caracteres
        payload = {
            "service_name": "Srv X",
            "description": long_description,
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'description' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-003.9",
            "400 – Longitud máxima de descripción superada (max_length=500)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected max length error for description, got: {response.data}"
    
    def test_invalid_tax_rate_with_applicable_tax(self):
        """UT-SER-003.10: 400 – Tasa de impuesto inválida cuando hay impuesto aplicable"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Srv X",
            "description": "x",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            ('tax_rate' in str(response.data.get('errors', {})) and
             'mayor a 0' in str(response.data.get('errors', {})))
        )
        
        Report.add(
            "UT-SER-003.10",
            "400 – Tasa de impuesto inválida cuando hay impuesto aplicable",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected invalid tax rate error, got: {response.data}"
    
    def test_vat_exempt_service(self):
        """UT-SER-003.11: 200 – Servicio exento de IVA (is_vat_exempt=true) ignora tax_rate"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Servicio Exento",
            "description": "x",
            "service_type": 17,
            "base_price": 1000.0,
            "price_unit": 17,
            "applicable_tax": 0,
            "tax_rate": 0,
            "is_vat_exempt": True
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            with patch('service_requests.api.service_viewset.get_actor_info', return_value=(1, "Test User", "Admin")):
                with patch('service_requests.api.service_viewset.AuditClient'):
                    response = self.client.patch(
                        endpoint,
                        data=json.dumps(payload),
                        content_type='application/json',
                    )
        
        approved = (
            response.status_code == 200 and
            response.data.get('success') is True and
            response.data.get('message') == "Servicio actualizado exitosamente"
        )
        
        Report.add(
            "UT-SER-003.11",
            "200 – Servicio exento de IVA (is_vat_exempt=true) ignora tax_rate",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected successful VAT exempt update, got: {response.data}"
    
    def test_insufficient_permissions(self):
        """UT-SER-003.12: 403 Forbidden – Usuario sin permiso service.update"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Srv X",
            "description": "x",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=False):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 403 and
            response.data.get('success') is False and
            'No tiene permisos para actualizar servicios' in str(response.data.get('message', ''))
        )
        
        Report.add(
            "UT-SER-003.12",
            "403 Forbidden – Usuario sin permiso service.update",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected forbidden error, got: {response.data}"
    
    def test_service_not_found(self):
        """UT-SER-003.13: 404 Not Found – Servicio no existe"""
        endpoint = '/services/9999/update/'
        payload = {
            "service_name": "Srv X",
            "description": "x",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code == 404 and
            response.data.get('success') is False and
            'Servicio no encontrado' in str(response.data.get('message', ''))
        )
        
        Report.add(
            "UT-SER-003.13",
            "404 Not Found – Servicio no existe",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected not found error, got: {response.data}"
    
    def test_database_error(self):
        """UT-SER-003.14: 500 / 503 – Error técnico al guardar (rollback)"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Srv X",
            "description": "x",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            with patch('service_requests.serializers.service_serializers.service_update_serializer.ServiceUpdateSerializer.save', side_effect=Exception("Database error")):
                response = self.client.patch(
                    endpoint,
                    data=json.dumps(payload),
                    content_type='application/json',
                )
        
        approved = (
            response.status_code in [500, 503] and
            response.data.get('success') is False and
            'Error al procesar la solicitud' in str(response.data.get('message', ''))
        )
        
        Report.add(
            "UT-SER-003.14",
            "500 / 503 – Error técnico al guardar (rollback)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected server error, got: {response.data}"
    
    def test_invalid_data_type(self):
        """UT-SER-003.15: 422 – Tipo de dato inválido (ej.: tax_rate string)"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Srv",
            "description": "x",
            "service_type": 17,
            "base_price": 1000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": "diecinueve",
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.patch(
                endpoint,
                data=json.dumps(payload),
                content_type='application/json',
            )
        
        approved = (
            response.status_code in [400, 422] and
            response.data.get('success') is False and
            'tax_rate' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-003.15",
            "422 – Tipo de dato inválido (ej.: tax_rate string)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected data type error, got: {response.data}"
    
    def test_partial_update(self):
        """UT-SER-003.16: 200 – Actualización parcial (solo algunos campos)"""
        endpoint = f'/services/{self.test_service.id_service}/update/'
        payload = {
            "service_name": "Nueva Descripción Solo",
            "description": "Solo cambio descripción"
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            with patch('service_requests.api.service_viewset.get_actor_info', return_value=(1, "Test User", "Admin")):
                with patch('service_requests.api.service_viewset.AuditClient'):
                    response = self.client.patch(
                        endpoint,
                        data=json.dumps(payload),
                        content_type='application/json',
                    )
        
        approved = (
            response.status_code == 200 and
            response.data.get('success') is True and
            response.data.get('message') == "Servicio actualizado exitosamente"
        )
        
        Report.add(
            "UT-SER-003.16",
            "200 – Actualización parcial (solo algunos campos)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected successful partial update, got: {response.data}"
