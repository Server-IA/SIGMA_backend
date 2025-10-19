# Test HU-PM-001 - Programar mantenimiento manual
import pytest
import os
import django
from django.test import TestCase
from django.utils import timezone

# Configurar Django antes de importar modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
django.setup()

@pytest.mark.django_db
class MaintenanceSchedulingCreateTestCase(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        from users.models.user import User
        from parameterization.models.statues_category import StatuesCategory
        from parameterization.models.statues import Statues
        from parameterization.models.brands_category import BrandsCategory
        from parameterization.models.brands import Brands
        from parameterization.models.brand_model import Models
        from parameterization.models.types_category import TypesCategory
        from parameterization.models.types import Types
        from machinery.models.machinery import Machinery
        from maintenance.models.maintenance_scheduling import MaintenanceScheduling
        from datetime import datetime, timedelta

        # Crear usuarios con y sin permisos
        self.user_with_permission = User.objects.create(id_user=101)
        self.user_without_permission = User.objects.create(id_user=102)

        # Crear StatuesCategory y estados parametrizados HU-PM-001: 13
        statues_category = StatuesCategory.objects.create(
            name="Estado Mantenimiento PM-001",
            description="Categoría de estados de mantenimiento",
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        # Estados según HU-PM-001
        self.status_programmed = Statues.objects.create(
            id_statues=13,
            name="Programado",
            description="Mantenimiento programado",
            id_statues_categories=statues_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        # Crear datos relacionados requeridos por el backend
        brands_category = BrandsCategory.objects.create(
            name="Categoría Marca PM-001",
            description="Categoría de marcas",
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        brand = Brands.objects.create(
            name="Marca Test PM-001",
            description="Marca de prueba",
            id_brands_categories=brands_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission,
            id_statues=self.status_programmed
        )

        model = Models.objects.create(
            name="Modelo Test PM-001",
            description="Modelo de prueba",
            id_brand=brand,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission,
            id_statues=self.status_programmed
        )
        


        # Crear categoría de tipos de mantenimiento (id=12)
        types_category = TypesCategory.objects.create(
            id_types_categories=12,
            name="Tipos de mantenimiento",
            description="Categoría de tipos de mantenimiento",
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        machine_type = Types.objects.create(
            name="Tipo Test PM-001",
            description="Tipo de maquina de prueba",
            id_types_categories=types_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission,
            id_statues=self.status_programmed
        )

        # Tipo de mantenimiento válido
        self.maintenance_type = Types.objects.create(
            id_types=35,
            name="Preventivo",
            description="Mantenimiento preventivo",
            id_types_categories=types_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission,
            id_statues=self.status_programmed
        )

        # Tipo de mantenimiento inválido (fuera de categoría id=12)
        other_category = TypesCategory.objects.create(
            name="Categoría Otro PM-001",
            description="Categoría de tipos otros",
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        self.invalid_type = Types.objects.create(
            id_types=999,
            name="Otro PM-001",
            description="Tipo inválido",
            id_types_categories=other_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission,
            id_statues=self.status_programmed
        )


        
        # Crear maquinaria con todos los campos requeridos
        machinery = Machinery.objects.create(
            machinery_name="Maquinaria Test PM-001",
            manufacturing_year=2020,
            serial_number="TESTPM001UNIQUE",
            machinery_type=machine_type,
            id_model_id=model.pk,
            tariff_subheading="",
            machinery_secondary_type=machine_type,
            id_city=1,
            image_path="",
            id_device=None,
            justification="Maquinaria de prueba PM-001",
            machinery_operational_status=self.status_programmed,
            id_responsible_user=self.user_with_permission
        )

        self.machinery = machinery

        # Crear técnico activo
        self.technician = User.objects.create(id_user=107)

        self.client = APIClient()
        self.create_url = "/maintenance_scheduling/create/"

    def _force_auth_with_permission(self, user, permission_id=117):
        """Simula JWT y permiso 117 para maintenance_scheduling.create"""
        # Autenticar usuario
        self.client.force_authenticate(user=user)
        
        # Mock directo de check_permission para simular que el usuario tiene el permiso
        from unittest.mock import patch
        from maintenance.api.maintenance_scheduling_viewset import MaintenanceSchedulingViewSet
        
        # Simular que check_permission siempre devuelve True para este usuario/permiso
        def mock_check_permission(viewset_self, request, required_permission_id):
            return required_permission_id == permission_id
        
        # Aplicar el patch
        self._permission_patch = patch.object(
            MaintenanceSchedulingViewSet, 
            'check_permission', 
            mock_check_permission
        )
        self._permission_patch.start()

    def tearDown(self):
        """Limpiar mocks después de cada test"""
        if hasattr(self, '_permission_patch'):
            self._permission_patch.stop()

    # TEST CASOS HU-PM-001

    def test_create_success_201(self):
        """Creación exitosa de mantenimiento programado"""
        from datetime import datetime, timedelta
        self._force_auth_with_permission(self.user_with_permission, 117)
        data = {
            "id_machinery": self.machinery.id_machinery,
            "scheduled_at": (timezone.now() + timedelta(hours=2)).isoformat(),
            "details": "Cambio de filtros y revisión de frenos",
            "assigned_technician": self.technician.id_user,
            "maintenance_type": self.maintenance_type.id_types
        }
        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get('success'))
        self.assertIn("id_maintenance_scheduling", response.data.get('data', {}))

    def test_create_past_date_422(self):
        """No permite programar en fecha pasada"""
        from datetime import datetime, timedelta
        self._force_auth_with_permission(self.user_with_permission, 117)
        data = {
            "id_machinery": self.machinery.id_machinery,
            "scheduled_at": (timezone.now() - timedelta(days=1)).isoformat(),
            "details": "Cambio de filtros y revisión de frenos",
            "assigned_technician": self.technician.id_user,
            "maintenance_type": self.maintenance_type.id_types
        }
        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, 422)
        self.assertIn("scheduled_at", str(response.data))

    def test_create_invalid_type_422(self):
        """No permite tipo de mantenimiento fuera de categoría id=12"""
        from datetime import datetime, timedelta
        self._force_auth_with_permission(self.user_with_permission, 117)
        data = {
            "id_machinery": self.machinery.id_machinery,
            "scheduled_at": (timezone.now() + timedelta(hours=2)).isoformat(),
            "details": "Cambio de filtros y revisión de frenos",
            "assigned_technician": self.technician.id_user,
            "maintenance_type": self.invalid_type.id_types
        }
        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, 422)
        self.assertIn("maintenance_type", str(response.data))

    def test_create_no_permission_403(self):
        """No permite crear sin permiso 117"""
        from datetime import datetime, timedelta
        self.client.force_authenticate(user=self.user_without_permission)
        data = {
            "id_machinery": self.machinery.id_machinery,
            "scheduled_at": (timezone.now() + timedelta(hours=2)).isoformat(),
            "details": "Cambio de filtros y revisión de frenos",
            "assigned_technician": self.technician.id_user,
            "maintenance_type": self.maintenance_type.id_types
        }
        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_create_technician_unavailable_422(self):
        """No permite programar si el técnico no está disponible"""
        from datetime import datetime, timedelta
        self._force_auth_with_permission(self.user_with_permission, 117)
        # Usar técnico inexistente para simular no disponible
        data = {
            "id_machinery": self.machinery.id_machinery,
            "scheduled_at": (timezone.now() + timedelta(hours=2)).isoformat(),
            "details": "Cambio de filtros y revisión de frenos",
            "assigned_technician": 999,  # Técnico inexistente
            "maintenance_type": self.maintenance_type.id_types
        }
        response = self.client.post(self.create_url, data, format='json')
        self.assertEqual(response.status_code, 422)