"""
Tests para el módulo de maquinaria
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from machinery.models import Machinery, MachineryTrackerSheet, MachineryUsageSheet
from parameterization.models import Brands, Models, EmployeeDepartment

User = get_user_model()


class MachineryModelTests(TestCase):
    """Tests para los modelos de maquinaria"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        from datetime import datetime
        from parameterization.models import BrandsCategory, Statues
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear datos de prueba para parametrización
        self.brands_category = BrandsCategory.objects.create(
            name='Maquinaria Pesada',
            description='Categoría de maquinaria pesada'
        )
        
        self.statues = Statues.objects.create(
            name='Activo',
            description='Estado activo'
        )
        
        self.brand = Brands.objects.create(
            name='Caterpillar',
            description='Marca de maquinaria pesada',
            id_brands_categories=self.brands_category,
            modification_date=datetime.now(),
            creation_date=datetime.now(),
            id_responsible_user=self.user,
            id_statues=self.statues
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
    
    def test_machinery_creation(self):
        """Test para crear una máquina"""
        machinery = Machinery.objects.create(
            name='Excavadora CAT 320',
            description='Excavadora para construcción',
            id_brands=self.brand,
            id_models=self.model,
            id_department=self.department,
            id_user=self.user
        )
        
        self.assertEqual(machinery.name, 'Excavadora CAT 320')
        self.assertEqual(machinery.id_brands, self.brand)
        self.assertEqual(machinery.id_models, self.model)
        self.assertTrue(machinery.is_active)
    
    def test_machinery_str_representation(self):
        """Test para la representación string de la máquina"""
        machinery = Machinery.objects.create(
            name='Excavadora CAT 320',
            id_brands=self.brand,
            id_models=self.model,
            id_department=self.department,
            id_user=self.user
        )
        
        self.assertEqual(str(machinery), 'Excavadora CAT 320')


class MachineryAPITests(APITestCase):
    """Tests para la API de maquinaria"""
    
    def setUp(self):
        """Configuración inicial para los tests de API"""
        from datetime import datetime
        from parameterization.models import BrandsCategory, Statues
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.brands_category = BrandsCategory.objects.create(
            name='Maquinaria Pesada',
            description='Categoría de maquinaria pesada'
        )
        
        self.statues = Statues.objects.create(
            name='Activo',
            description='Estado activo'
        )
        
        self.brand = Brands.objects.create(
            name='Caterpillar',
            description='Marca de maquinaria pesada',
            id_brands_categories=self.brands_category,
            modification_date=datetime.now(),
            creation_date=datetime.now(),
            id_responsible_user=self.user,
            id_statues=self.statues
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
        
        self.machinery = Machinery.objects.create(
            name='Excavadora CAT 320',
            description='Excavadora para construcción',
            id_brands=self.brand,
            id_models=self.model,
            id_department=self.department,
            id_user=self.user
        )
    
    def test_machinery_list_api(self):
        """Test para listar máquinas via API"""
        url = reverse('machinery-list')
        response = self.client.get(url)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_machinery_creation_api(self):
        """Test para crear máquina via API"""
        url = reverse('machinery-list')
        data = {
            'name': 'Nueva Excavadora',
            'description': 'Descripción de la nueva excavadora',
            'id_brands': self.brand.id,
            'id_models': self.model.id,
            'id_department': self.department.id
        }
        
        response = self.client.post(url, data)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MachineryTrackerSheetTests(TestCase):
    """Tests para las hojas de seguimiento de maquinaria"""
    
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
        
        self.machinery = Machinery.objects.create(
            name='Excavadora CAT 320',
            id_brands=self.brand,
            id_models=self.model,
            id_department=self.department,
            id_user=self.user
        )
    
    def test_tracker_sheet_creation(self):
        """Test para crear una hoja de seguimiento"""
        tracker_sheet = MachineryTrackerSheet.objects.create(
            id_machinery=self.machinery,
            id_user=self.user,
            description='Seguimiento de mantenimiento'
        )
        
        self.assertEqual(tracker_sheet.id_machinery, self.machinery)
        self.assertEqual(tracker_sheet.id_user, self.user)
        self.assertEqual(tracker_sheet.description, 'Seguimiento de mantenimiento')
