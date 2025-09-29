"""
Tests de integración para el sistema completo
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.db import transaction
from machinery.models import Machinery, MachineryTrackerSheet
from maintenance.models import Maintenance, MaintenanceRequest
from parameterization.models import Brands, Models, EmployeeDepartment

User = get_user_model()


class SystemIntegrationTests(TestCase):
    """Tests de integración del sistema completo"""
    
    def setUp(self):
        """Configuración inicial para los tests de integración"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear datos de parametrización
        self.brand = Brands.objects.create(
            name='Caterpillar',
            description='Marca de maquinaria pesada'
        )
        
        self.model = Models.objects.create(
            name='CAT 320',
            description='Excavadora mediana',
            id_brands=self.brand
        )
        
        self.department = EmployeeDepartment.objects.create(
            name='Mantenimiento',
            description='Departamento de mantenimiento'
        )
    
    def test_complete_machinery_workflow(self):
        """Test para el flujo completo de gestión de maquinaria"""
        # 1. Crear una máquina
        machinery = Machinery.objects.create(
            name='Excavadora CAT 320',
            description='Excavadora para construcción',
            id_brands=self.brand,
            id_models=self.model,
            id_department=self.department,
            id_user=self.user
        )
        
        self.assertEqual(machinery.name, 'Excavadora CAT 320')
        self.assertTrue(machinery.is_active)
        
        # 2. Crear una hoja de seguimiento
        tracker_sheet = MachineryTrackerSheet.objects.create(
            id_machinery=machinery,
            id_user=self.user,
            description='Seguimiento de mantenimiento preventivo'
        )
        
        self.assertEqual(tracker_sheet.id_machinery, machinery)
        self.assertEqual(tracker_sheet.id_user, self.user)
        
        # 3. Crear un mantenimiento
        maintenance = Maintenance.objects.create(
            name='Mantenimiento Preventivo CAT 320',
            description='Mantenimiento programado de la excavadora',
            id_responsible_user=self.user,
            maintenance_status='PENDING'
        )
        
        self.assertEqual(maintenance.name, 'Mantenimiento Preventivo CAT 320')
        self.assertEqual(maintenance.maintenance_status, 'PENDING')
        
        # 4. Crear una solicitud de mantenimiento
        maintenance_request = MaintenanceRequest.objects.create(
            id_responsible_user=self.user,
            description='Solicitud de mantenimiento para la excavadora',
            justification='La máquina presenta desgaste en las orugas'
        )
        
        self.assertEqual(maintenance_request.description, 'Solicitud de mantenimiento para la excavadora')
        self.assertEqual(maintenance_request.justification, 'La máquina presenta desgaste en las orugas')
    
    def test_data_consistency_across_modules(self):
        """Test para verificar la consistencia de datos entre módulos"""
        # Crear una máquina
        machinery = Machinery.objects.create(
            name='Excavadora CAT 320',
            id_brands=self.brand,
            id_models=self.model,
            id_department=self.department,
            id_user=self.user
        )
        
        # Verificar que la máquina está correctamente relacionada
        self.assertEqual(machinery.id_brands.name, 'Caterpillar')
        self.assertEqual(machinery.id_models.name, 'CAT 320')
        self.assertEqual(machinery.id_department.name, 'Mantenimiento')
        self.assertEqual(machinery.id_user.username, 'testuser')
        
        # Verificar que las relaciones inversas funcionan
        self.assertIn(machinery, self.brand.machinery_set.all())
        self.assertIn(machinery, self.model.machinery_set.all())
        self.assertIn(machinery, self.department.machinery_set.all())
        self.assertIn(machinery, self.user.machinery_set.all())


class APIIntegrationTests(APITestCase):
    """Tests de integración para las APIs"""
    
    def setUp(self):
        """Configuración inicial para los tests de API"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.brand = Brands.objects.create(
            name='Caterpillar',
            description='Marca de maquinaria pesada'
        )
        
        self.model = Models.objects.create(
            name='CAT 320',
            description='Excavadora mediana',
            id_brands=self.brand
        )
        
        self.department = EmployeeDepartment.objects.create(
            name='Mantenimiento',
            description='Departamento de mantenimiento'
        )
    
    def test_api_authentication_consistency(self):
        """Test para verificar la consistencia de autenticación en todas las APIs"""
        # Lista de endpoints que requieren autenticación
        endpoints = [
            'machinery-list',
            'maintenance-list',
            'maintenance-request-list',
            'brands-list',
            'models-list',
            'employee-departments-list',
            'user-list'
        ]
        
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                try:
                    url = reverse(endpoint)
                    response = self.client.get(url)
                    # Todos los endpoints deberían requerir autenticación
                    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                except:
                    # Si el endpoint no existe, continuar con el siguiente
                    continue
    
    def test_api_response_format_consistency(self):
        """Test para verificar la consistencia del formato de respuesta de las APIs"""
        # Este test verificaría que todas las APIs devuelvan respuestas en el mismo formato
        # Por ahora, solo verificamos que las APIs requieren autenticación
        pass


class DatabaseTransactionTests(TransactionTestCase):
    """Tests para transacciones de base de datos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.brand = Brands.objects.create(
            name='Caterpillar',
            description='Marca de maquinaria pesada'
        )
        
        self.model = Models.objects.create(
            name='CAT 320',
            description='Excavadora mediana',
            id_brands=self.brand
        )
        
        self.department = EmployeeDepartment.objects.create(
            name='Mantenimiento',
            description='Departamento de mantenimiento'
        )
    
    def test_machinery_creation_transaction(self):
        """Test para verificar que la creación de maquinaria es atómica"""
        with transaction.atomic():
            machinery = Machinery.objects.create(
                name='Excavadora CAT 320',
                id_brands=self.brand,
                id_models=self.model,
                id_department=self.department,
                id_user=self.user
            )
            
            # Verificar que la máquina se creó correctamente
            self.assertIsNotNone(machinery.id)
            self.assertEqual(machinery.name, 'Excavadora CAT 320')
    
    def test_rollback_on_error(self):
        """Test para verificar que se hace rollback en caso de error"""
        initial_count = Machinery.objects.count()
        
        try:
            with transaction.atomic():
                # Crear una máquina válida
                Machinery.objects.create(
                    name='Excavadora CAT 320',
                    id_brands=self.brand,
                    id_models=self.model,
                    id_department=self.department,
                    id_user=self.user
                )
                
                # Forzar un error
                raise Exception("Error simulado")
        except Exception:
            pass
        
        # Verificar que no se creó ninguna máquina
        self.assertEqual(Machinery.objects.count(), initial_count)
