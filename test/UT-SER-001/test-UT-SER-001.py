"""
Pruebas unitarias para el endpoint de creación de servicios
ID: UT-SER-001 (RF-062)
"""

import os
import sys
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Configuración de Django ANTES de cualquier import de Django/DRF
if '/app' not in sys.path:
    sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')

import django
django.setup()

# AHORA sí podemos importar Django/DRF
from django.utils import timezone
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
        
        report = f"""# Reporte de Pruebas Unitarias - UT-SER-001

## Resumen Ejecutivo
- **Total de Pruebas**: {total_tests}
- **Pruebas Exitosas**: {passed_tests} ✅
- **Pruebas Fallidas**: {failed_tests} ❌
- **Tasa de Éxito**: {success_rate:.1f}%
- **Fecha de Ejecución**: {datetime.now().strftime('%d/%m/%Y')}
- **Ejecutado por**: Sistema de Pruebas Automatizadas

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

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

"""
        
        return report


@pytest.fixture(scope='module', autouse=True)
def _write_report_on_module_end():
    Report.rows = []
    yield
    # Generar reporte al final del módulo
    report_content = Report.generate_markdown_report()
    with open('test/UT-SER-001/reporte_UT_SER_001_RF_062.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"\n📊 Reporte generado: test/UT-SER-001/reporte_UT_SER_001_RF_062.md")


@pytest.mark.django_db
class TestServiceCreation:
    endpoint = '/services/create/'
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Configura datos de prueba necesarios"""
        # Crear categorías usando get_or_create para evitar duplicados
        self.service_category, _ = TypesCategory.objects.get_or_create(
            id_types_categories=14,
            defaults={
                'name': "Tipos de servicios",
                'description': "Categoría para tipos de servicios",
                'creation_date': timezone.now(),
                'modification_date': timezone.now()
            }
        )
        
        self.currency_category, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=10,
            defaults={
                'name': "Unidades de moneda",
                'description': "Categoría para unidades de moneda",
                'creation_date': timezone.now(),
                'modification_date': timezone.now()
            }
        )
        
        self.status_category, _ = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                'name': "Estados de servicios",
                'description': "Categoría para estados de servicios",
                'creation_date': timezone.now(),
                'modification_date': timezone.now()
            }
        )
        
        # Crear estado activo primero
        self.active_status, _ = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                'name': "Activo",
                'description': "Estado activo del servicio",
                'id_statues_categories': self.status_category,
                'creation_date': timezone.now(),
                'modification_date': timezone.now()
            }
        )
        
        # Crear tipos de servicio
        self.service_type, _ = Types.objects.get_or_create(
            id_types=17,
            defaults={
                'name': "Mantenimiento Preventivo",
                'description': "Tipo de servicio de mantenimiento preventivo",
                'id_types_categories': self.service_category,
                'creation_date': timezone.now(),
                'modification_date': timezone.now(),
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
                'creation_date': timezone.now(),
                'modification_date': timezone.now()
            }
        )
        
        # Crear usuario de prueba
        self.test_user, _ = User.objects.get_or_create(id_user=1)
        
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
                "permisos": [{"id": 140, "name": "service.create"}]
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
    
    def test_successful_service_creation(self):
        """UT-SER-001: Creación exitosa de servicio"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
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
                    response = self.client.post(
                        self.endpoint,
                        data=json.dumps(payload),
                        content_type='application/json',
                    )
        
        # Verificar respuesta
        approved = (
            response.status_code in [200, 201] and
            response.data.get('success') is True and
            response.data.get('message') == "Servicio creado exitosamente" and
            response.data.get('service_id') is not None and
            response.data.get('service_id') > 0
        )
        
        Report.add(
            "UT-SER-001",
            "201 Created – Registro exitoso (camino feliz)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected successful creation, got: {response.data}"
    
    def test_missing_service_name(self):
        """UT-SER-001.1: Campo service_name vacío"""
        payload = {
            "service_name": "",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'service_name' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.1",
            "400 Bad Request – Campo service_name vacío",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for empty service_name, got: {response.data}"
    
    def test_missing_service_type(self):
        """UT-SER-001.2: Campo service_type nulo"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": None,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'service_type' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.2",
            "400 Bad Request – Campo service_type nulo",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for null service_type, got: {response.data}"
    
    def test_missing_base_price(self):
        """UT-SER-001.3: Campo base_price nulo"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": None,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'base_price' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.3",
            "400 Bad Request – Campo base_price nulo",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for null base_price, got: {response.data}"
    
    def test_missing_price_unit(self):
        """UT-SER-001.4: Campo price_unit nulo"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": None,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'price_unit' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.4",
            "400 Bad Request – Campo price_unit nulo",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for null price_unit, got: {response.data}"
    
    def test_missing_applicable_tax(self):
        """UT-SER-001.5: Campo applicable_tax nulo"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": None,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'applicable_tax' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.5",
            "400 Bad Request – Campo applicable_tax nulo",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for null applicable_tax, got: {response.data}"
    
    def test_duplicate_service_name(self):
        """UT-SER-001.6: Nombre de servicio duplicado"""
        # Crear servicio existente usando get_or_create
        existing_service, _ = Service.objects.get_or_create(
            service_name="Mantenimiento Preventivo Estándar",
            defaults={
                'description': "Servicio existente",
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
        
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'Ya existe un servicio con este nombre' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.6",
            "400 Bad Request – Nombre de servicio duplicado",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected duplicate name error, got: {response.data}"
    
    def test_zero_base_price(self):
        """UT-SER-001.7: Precio base igual a 0"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 0.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'El precio base debe ser mayor a 0' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.7",
            "400 Bad Request – Precio base igual a 0",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for zero price, got: {response.data}"
    
    def test_negative_base_price(self):
        """UT-SER-001.8: Precio base negativo"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": -100.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'El precio base debe ser mayor a 0' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.8",
            "400 Bad Request – Precio base negativo",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for negative price, got: {response.data}"
    
    def test_invalid_service_type_category(self):
        """UT-SER-001.9: Tipo de servicio de categoría incorrecta"""
        # Crear tipo de servicio en categoría incorrecta
        wrong_category, _ = TypesCategory.objects.get_or_create(
            id_types_categories=99,
            defaults={
                'name': "Categoría Incorrecta",
                'description': "Categoría que no es de servicios",
                'creation_date': timezone.now(),
                'modification_date': timezone.now()
            }
        )
        
        wrong_type, _ = Types.objects.get_or_create(
            id_types=99,
            defaults={
                'name': "Tipo Incorrecto",
                'description': "Tipo que no pertenece a servicios",
                'id_types_categories': wrong_category,
                'creation_date': timezone.now(),
                'modification_date': timezone.now(),
                'id_statues': self.active_status
            }
        )
        
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 99,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False
        )
        
        Report.add(
            "UT-SER-001.9",
            "400 Bad Request – Tipo de servicio de categoría incorrecta",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for wrong service type category, got: {response.data}"
    
    def test_invalid_price_unit_category(self):
        """UT-SER-001.10: Unidad de precio de categoría incorrecta"""
        # Crear unidad de precio en categoría incorrecta
        wrong_units_category, _ = UnitsCategory.objects.get_or_create(
            id_units_categories=99,
            defaults={
                'name': "Categoría Incorrecta",
                'description': "Categoría que no es de moneda",
                'creation_date': timezone.now(),
                'modification_date': timezone.now()
            }
        )
        
        wrong_unit, _ = Units.objects.get_or_create(
            id_units=99,
            defaults={
                'name': "Unidad Incorrecta",
                'symbol': "INC",
                'id_units_categories': wrong_units_category,
                'id_types': self.service_type,
                'id_statues': self.active_status,
                'creation_date': timezone.now(),
                'modification_date': timezone.now()
            }
        )
        
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 99,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False
        )
        
        Report.add(
            "UT-SER-001.10",
            "400 Bad Request – Unidad de precio de categoría incorrecta",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for wrong price unit category, got: {response.data}"
    
    def test_service_name_too_long(self):
        """UT-SER-001.11: Nombre de servicio con más de 100 caracteres"""
        long_name = "A" * 101  # 101 caracteres
        
        payload = {
            "service_name": long_name,
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'service_name' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.11",
            "400 Bad Request – Nombre de servicio muy largo (101 caracteres)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for long service name, got: {response.data}"
    
    def test_description_too_long(self):
        """UT-SER-001.12: Descripción con más de 500 caracteres"""
        long_description = "A" * 501  # 501 caracteres
        
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": long_description,
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 400 and
            response.data.get('success') is False and
            'description' in str(response.data.get('errors', {}))
        )
        
        Report.add(
            "UT-SER-001.12",
            "400 Bad Request – Descripción muy larga (501 caracteres)",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected validation error for long description, got: {response.data}"
    
    def test_unauthorized_user(self):
        """UT-SER-001.13: Usuario no autenticado"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }

        # Crear un cliente sin autenticación
        unauth_client = APIClient()
        response = unauth_client.post(
            self.endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        approved = (
            response.status_code == 401 and
            ('Usuario no autenticado' in str(response.data) or 
             'Authentication credentials were not provided' in str(response.data))
        )
        
        Report.add(
            "UT-SER-001.13",
            "401 Unauthorized – Usuario no autenticado",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected unauthorized error, got: {response.data}"
    
    def test_insufficient_permissions(self):
        """UT-SER-001.14: Usuario sin permisos suficientes"""
        payload = {
            "service_name": "Mantenimiento Preventivo Estándar",
            "description": "Servicio de mantenimiento preventivo estándar",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=False):
            response = self.client.post(
                self.endpoint,
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_AUTHORIZATION=f'Bearer mock_token'
            )
        
        approved = (
            response.status_code == 403 and
            'No tiene permisos para crear un servicio' in str(response.data)
        )
        
        Report.add(
            "UT-SER-001.14",
            "403 Forbidden – Usuario sin permisos suficientes",
            payload,
            response.status_code,
            response.data,
            approved
        )
        
        assert approved, f"Expected forbidden error, got: {response.data}"
    
    def test_response_time_performance(self):
        """UT-SER-001.15: Tiempo de respuesta menor a 3 segundos"""
        import time
        
        payload = {
            "service_name": "Servicio de Prueba Performance",
            "description": "Servicio de prueba para medir rendimiento",
            "service_type": 17,
            "base_price": 150000.0,
            "price_unit": 17,
            "applicable_tax": 1,
            "tax_rate": 19.0,
            "is_vat_exempt": False
        }
        
        start_time = time.time()
        
        with patch('service_requests.api.service_viewset.ServiceViewSet.check_permission', return_value=True):
            with patch('service_requests.api.service_viewset.get_actor_info', return_value=(1, "Test User", "Admin")):
                with patch('service_requests.api.service_viewset.AuditClient'):
                    response = self.client.post(
                        self.endpoint,
                        data=json.dumps(payload),
                        content_type='application/json',
                    )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        approved = (
            response.status_code in [200, 201] and
            response_time < 3.0
        )
        
        # Debug: print response details if test fails
        if not approved:
            print(f"Performance test failed: Status={response.status_code}, Time={response_time:.3f}s, Response={response.data}")
        
        Report.add(
            "UT-SER-001.15",
            f"Performance – Tiempo de respuesta: {response_time:.3f}s (límite: 3s)",
            payload,
            response.status_code,
            {"response_time": response_time, "response": response.data},
            approved
        )
        
        assert approved, f"Expected response time < 3s, got: {response_time:.3f}s"
