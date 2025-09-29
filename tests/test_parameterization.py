"""
Tests para el módulo de parametrización
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from parameterization.models import (
    Brands, Models, EmployeeDepartment, EmployeeCharge,
    Units, UnitsCategory, Types, TypesCategory,
    Statues, StatuesCategory, VisualParameterization
)

User = get_user_model()


class ParameterizationModelTests(TestCase):
    """Tests para los modelos de parametrización"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
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
        department = EmployeeDepartment.objects.create(
            name='Mantenimiento',
            description='Departamento de mantenimiento'
        )
        
        self.assertEqual(department.name, 'Mantenimiento')
        self.assertEqual(department.description, 'Departamento de mantenimiento')
        self.assertTrue(department.is_active)
    
    def test_employee_charges_creation(self):
        """Test para crear un cargo de empleado"""
        charge = EmployeeCharges.objects.create(
            name='Técnico de Mantenimiento',
            description='Técnico especializado en mantenimiento'
        )
        
        self.assertEqual(charge.name, 'Técnico de Mantenimiento')
        self.assertEqual(charge.description, 'Técnico especializado en mantenimiento')
        self.assertTrue(charge.is_active)
    
    def test_units_creation(self):
        """Test para crear una unidad"""
        units_category = UnitsCategory.objects.create(
            name='Longitud',
            description='Unidades de medida de longitud'
        )
        
        unit = Units.objects.create(
            name='Metro',
            symbol='m',
            id_types=units_category
        )
        
        self.assertEqual(unit.name, 'Metro')
        self.assertEqual(unit.symbol, 'm')
        self.assertEqual(unit.id_types, units_category)
        self.assertTrue(unit.is_active)
    
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
    
    def test_models_list_api(self):
        """Test para listar modelos via API"""
        url = reverse('models-list')
        response = self.client.get(url)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_employee_departments_list_api(self):
        """Test para listar departamentos via API"""
        url = reverse('employee-departments-list')
        response = self.client.get(url)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ParameterizationBusinessLogicTests(TestCase):
    """Tests para la lógica de negocio de parametrización"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_brand_model_relationship(self):
        """Test para la relación entre marca y modelo"""
        brand = Brands.objects.create(
            name='Caterpillar',
            description='Marca de maquinaria pesada'
        )
        
        model = Models.objects.create(
            name='CAT 320',
            description='Excavadora mediana',
            id_brands=brand
        )
        
        # Verificar la relación
        self.assertEqual(model.id_brands, brand)
        self.assertIn(model, brand.models_set.all())
    
    def test_units_category_relationship(self):
        """Test para la relación entre categoría de unidades y unidades"""
        category = UnitsCategory.objects.create(
            name='Longitud',
            description='Unidades de medida de longitud'
        )
        
        unit1 = Units.objects.create(
            name='Metro',
            symbol='m',
            id_types=category
        )
        
        unit2 = Units.objects.create(
            name='Centímetro',
            symbol='cm',
            id_types=category
        )
        
        # Verificar las relaciones
        self.assertEqual(unit1.id_types, category)
        self.assertEqual(unit2.id_types, category)
        self.assertIn(unit1, category.units_set.all())
        self.assertIn(unit2, category.units_set.all())
    
    def test_visual_parameterization_defaults(self):
        """Test para los valores por defecto de parametrización visual"""
        visual_param = VisualParameterization.objects.create()
        
        # Verificar que se crean con valores por defecto
        self.assertIsNotNone(visual_param.primary_color)
        self.assertIsNotNone(visual_param.secondary_color)
        self.assertIsNotNone(visual_param.accent_color)
