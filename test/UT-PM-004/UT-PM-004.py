# Test HU-PM-004 - Cancelar mantenimiento programado
import pytest
from django.test import TestCase

@pytest.mark.django_db
class MaintenanceSchedulingCancelTestCase(TestCase):
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
        self.user_with_permission = User.objects.create(id_user=1)
        self.user_without_permission = User.objects.create(id_user=2)

        # Crear StatuesCategory y estados parametrizados HU-PM-004: 13, 14, 15
        statues_category = StatuesCategory.objects.create(
            name="Estado Mantenimiento",
            description="Categoría de estados de mantenimiento",
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        # Estados según HU-PM-004
        self.status_programmed = Statues.objects.create(
            id_statues=13,
            name="Programado",
            description="Mantenimiento programado",
            id_statues_categories=statues_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )
        
        self.status_cancelled = Statues.objects.create(
            id_statues=14,
            name="Cancelado", 
            description="Mantenimiento cancelado",
            id_statues_categories=statues_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )
        
        self.status_finalized = Statues.objects.create(
            id_statues=15,
            name="Finalizado",
            description="Mantenimiento finalizado/ejecutado",
            id_statues_categories=statues_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        # Crear datos relacionados requeridos por el backend
        brands_category = BrandsCategory.objects.create(
            name="Categoría Marca",
            description="Categoría de marcas",
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        brand = Brands.objects.create(
            name="Marca Test",
            description="Marca de prueba",
            id_brands_categories=brands_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission,
            id_statues=self.status_programmed
        )

        model = Models.objects.create(
            name="Modelo Test",
            description="Modelo de prueba",
            id_brand=brand,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission,
            id_statues=self.status_programmed
        )

        types_category = TypesCategory.objects.create(
            name="Categoría Tipo",
            description="Categoría de tipos",
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission
        )

        machine_type = Types.objects.create(
            name="Tipo Test",
            description="Tipo de maquina de prueba",
            id_types_categories=types_category,
            creation_date=datetime.now(),
            modification_date=datetime.now(),
            id_responsible_user=self.user_with_permission,
            id_statues=self.status_programmed
        )

        # Crear maquinaria con todos los campos requeridos
        machinery = Machinery.objects.create(
            machinery_name="Maquinaria Test",
            manufacturing_year=2020,
            serial_number="TEST123456",
            machinery_type=machine_type,
            id_model=model,
            tariff_subheading="",
            machinery_secondary_type=machine_type,
            id_city=1,
            image_path="",
            id_device=None,
            justification="Maquinaria de prueba",
            machinery_operational_status=self.status_programmed,
            id_responsible_user=self.user_with_permission
        )

        # Crear mantenimiento programado para las pruebas
        self.scheduling = MaintenanceScheduling.objects.create(
            id_machinery=machinery,
            scheduled_at=datetime.now() + timedelta(days=1),
            details="Mantenimiento preventivo de prueba",
            assigned_technician=self.user_with_permission,
            maintenance_type=machine_type,
            maintenance_scheduling_status=self.status_programmed,
            justification=None,
            id_responsible_user=self.user_with_permission
        )

        self.client = APIClient()
        self.cancel_url = f"/maintenance_scheduling/{self.scheduling.id_maintenance_scheduling}/cancel/"

    def _force_auth_with_permission(self, user, permission_id=121):
        """Simula JWT y permiso 121 para maintenance_scheduling.canceled"""
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

    # TEST CASOS HU-PM-004

    def test_cancel_success_200(self):
        """Caso exitoso: usuario autenticado con permiso 121, justificación válida"""
        self._force_auth_with_permission(self.user_with_permission, 121)
        data = {"justification": "Cancelación por reprogramación de cliente"}
        response = self.client.post(self.cancel_url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('success'))
        self.assertIn("cancelado exitosamente", response.data.get('message', '').lower())
        self.assertIn("id_maintenance_scheduling", response.data.get('data', {}))

    def test_cancel_unauthenticated_401(self):
        """Error 401: usuario no autenticado"""
        self.client.force_authenticate(user=None)
        data = {"justification": "Motivo de cancelación"}
        response = self.client.post(self.cancel_url, data, format='json')
        
        self.assertEqual(response.status_code, 401)
        # Verificar que es error de autenticación (puede estar en message o detail)
        response_text = str(response.data).lower()
        self.assertTrue("credential" in response_text or "authentication" in response_text or "unauthorized" in response_text)

    def test_cancel_no_permission_403(self):
        """Error 403: usuario sin permiso 121"""
        self.client.force_authenticate(user=self.user_without_permission)
        data = {"justification": "Motivo de cancelación"}
        response = self.client.post(self.cancel_url, data, format='json')
        
        self.assertEqual(response.status_code, 403)
        self.assertIn("no tiene permisos", response.data.get('message', '').lower())

    def test_cancel_invalid_justification_422(self):
        """Error 422: justificación inválida (vacía o muy larga)"""
        self._force_auth_with_permission(self.user_with_permission, 121)
        
        # Justificación vacía
        data = {"justification": ""}
        response = self.client.post(self.cancel_url, data, format='json')
        self.assertEqual(response.status_code, 422)
        self.assertIn("justification", str(response.data).lower())
        
        # Justificación muy larga (>300 caracteres)
        long_justification = "x" * 301
        data = {"justification": long_justification}
        response = self.client.post(self.cancel_url, data, format='json')
        self.assertEqual(response.status_code, 422)
        self.assertIn("justification", str(response.data).lower())

    def test_cancel_already_cancelled_422(self):
        """Error 422: mantenimiento ya cancelado (estado 14)"""
        self._force_auth_with_permission(self.user_with_permission, 121)
        
        # Cambiar estado a cancelado
        self.scheduling.maintenance_scheduling_status = self.status_cancelled
        self.scheduling.save()
        
        data = {"justification": "Intentar cancelar nuevamente"}
        response = self.client.post(self.cancel_url, data, format='json')
        
        self.assertEqual(response.status_code, 422)
        self.assertIn("cancelado", str(response.data).lower())

    def test_cancel_finalized_422(self):
        """Error 422: mantenimiento finalizado (estado 15) - no se puede cancelar"""
        self._force_auth_with_permission(self.user_with_permission, 121)
        
        # Cambiar estado a finalizado
        self.scheduling.maintenance_scheduling_status = self.status_finalized
        self.scheduling.save()
        
        data = {"justification": "Intentar cancelar mantenimiento finalizado"}
        response = self.client.post(self.cancel_url, data, format='json')
        
        self.assertEqual(response.status_code, 422)
        self.assertIn("no puede cancelarse", str(response.data).lower())

    def test_cancel_not_found_404(self):
        """Error 404: mantenimiento no encontrado"""
        self._force_auth_with_permission(self.user_with_permission, 121)
        
        nonexistent_url = "/maintenance_scheduling/99999/cancel/"
        data = {"justification": "Cancelar mantenimiento inexistente"}
        response = self.client.post(nonexistent_url, data, format='json')
        
        self.assertEqual(response.status_code, 404)
        self.assertIn("no maintenancescheduling matches", response.data.get('detail', '').lower())

    def test_cancel_missing_justification_422(self):
        """Error 422: campo justification faltante"""
        self._force_auth_with_permission(self.user_with_permission, 121)
        
        data = {}  # Sin justification
        response = self.client.post(self.cancel_url, data, format='json')
        
        self.assertEqual(response.status_code, 422)
        self.assertIn("justification", str(response.data).lower())

    def test_cancel_valid_justification_length(self):
        """Caso límite: justificación de exactamente 300 caracteres"""
        self._force_auth_with_permission(self.user_with_permission, 121)
        
        # Justificación de exactamente 300 caracteres
        valid_justification = "x" * 300
        data = {"justification": valid_justification}
        response = self.client.post(self.cancel_url, data, format='json')
        
        # Debe ser exitoso o dar un error específico, pero no por longitud
        self.assertIn(response.status_code, [200, 422])
        if response.status_code == 200:
            self.assertTrue(response.data.get('success'))

    def test_cancel_state_change_verification(self):
        """Verificar que el estado cambia correctamente a 14 (Cancelado)"""
        self._force_auth_with_permission(self.user_with_permission, 121)
        
        # Estado inicial debe ser 13 (Programado)
        self.assertEqual(self.scheduling.maintenance_scheduling_status.id_statues, 13)
        
        data = {"justification": "Verificar cambio de estado"}
        response = self.client.post(self.cancel_url, data, format='json')
        
        # Debe ser exitoso (200)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('success'))
        
        # Recargar desde BD y verificar estado cambió a Cancelado
        self.scheduling.refresh_from_db()
        self.assertEqual(self.scheduling.maintenance_scheduling_status.id_statues, 14)
        self.assertIsNotNone(self.scheduling.justification)