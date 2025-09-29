from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from parameterization.models import (
    Brands, Models, EmployeeDepartments, EmployeeCharges,
    Units, UnitsCategory, Types, TypesCategory,
    Statues, StatuesCategory, VisualParameterization
)

User = get_user_model()


class ParameterizationModelTests(TestCase):
    """Tests para los modelos de parametrización"""
    
    def test_brands_creation(self):
        """Test para crear una marca"""
        brand = Brands.objects.create(
            name='Caterpillar',
            description='Marca de maquinaria pesada'
        )
        
        self.assertEqual(brand.name, 'Caterpillar')
        self.assertEqual(brand.description, 'Marca de maquinaria pesada')
        self.assertTrue(brand.is_active)
    
    def test_models_creation(self):
        """Test para crear un modelo"""
        brand = Brands.objects.create(
            name='Caterpillar',
            description='Marca de maquinaria pesada'
        )
        
        model = Models.objects.create(
            name='CAT 320',
            description='Excavadora mediana',
            id_brands=brand
        )
        
        self.assertEqual(model.name, 'CAT 320')
        self.assertEqual(model.id_brands, brand)
        self.assertTrue(model.is_active)
    
    def test_employee_departments_creation(self):
        """Test para crear un departamento de empleados"""
        department = EmployeeDepartments.objects.create(
            name='Mantenimiento',
            description='Departamento de mantenimiento'
        )
        
        self.assertEqual(department.name, 'Mantenimiento')
        self.assertEqual(department.description, 'Departamento de mantenimiento')
        self.assertTrue(department.is_active)
    
    def test_visual_parameterization_creation(self):
        """Test para crear parametrización visual"""
        visual_param = VisualParameterization.objects.create(
            primary_color='#007bff',
            secondary_color='#6c757d',
            accent_color='#28a745'
        )
        
        self.assertEqual(visual_param.primary_color, '#007bff')
        self.assertEqual(visual_param.secondary_color, '#6c757d')
        self.assertEqual(visual_param.accent_color, '#28a745')


class ParameterizationAPITests(APITestCase):
    """Tests para la API de parametrización"""
    
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
    
    def test_brands_list_api(self):
        """Test para listar marcas via API"""
        url = reverse('brands-list')
        response = self.client.get(url)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_brands_creation_api(self):
        """Test para crear marca via API"""
        url = reverse('brands-list')
        data = {
            'name': 'Nueva Marca',
            'description': 'Descripción de la nueva marca'
        }
        
        response = self.client.post(url, data)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
