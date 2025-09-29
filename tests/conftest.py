"""
Configuración de pytest para el proyecto
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from parameterization.models import Brands, Models, EmployeeDepartment

User = get_user_model()


@pytest.fixture
def test_user():
    """Fixture para crear un usuario de prueba"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_superuser():
    """Fixture para crear un superusuario de prueba"""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def test_brand():
    """Fixture para crear una marca de prueba"""
    return Brands.objects.create(
        name='Caterpillar',
        description='Marca de maquinaria pesada'
    )


@pytest.fixture
def test_model(test_brand):
    """Fixture para crear un modelo de prueba"""
    return Models.objects.create(
        name='CAT 320',
        description='Excavadora mediana',
        id_brands=test_brand
    )


@pytest.fixture
def test_department():
    """Fixture para crear un departamento de prueba"""
    return EmployeeDepartment.objects.create(
        name='Mantenimiento',
        description='Departamento de mantenimiento'
    )


@pytest.fixture
def test_machinery(test_user, test_brand, test_model, test_department):
    """Fixture para crear una máquina de prueba"""
    from machinery.models import Machinery
    
    return Machinery.objects.create(
        name='Excavadora CAT 320',
        description='Excavadora para construcción',
        id_brands=test_brand,
        id_models=test_model,
        id_department=test_department,
        id_user=test_user
    )


@pytest.fixture
def test_maintenance(test_user):
    """Fixture para crear un mantenimiento de prueba"""
    from maintenance.models import Maintenance
    
    return Maintenance.objects.create(
        name='Mantenimiento Preventivo',
        description='Mantenimiento programado',
        id_responsible_user=test_user,
        maintenance_status='PENDING'
    )


@pytest.fixture
def api_client():
    """Fixture para cliente de API de prueba"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_api_client(test_user):
    """Fixture para cliente de API autenticado"""
    from rest_framework.test import APIClient
    from rest_framework.authtoken.models import Token
    
    client = APIClient()
    token, created = Token.objects.get_or_create(user=test_user)
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    return client
