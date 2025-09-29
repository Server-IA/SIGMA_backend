"""
Tests para el módulo de mantenimiento
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from maintenance.models import Maintenance, MaintenanceRequest, MaintenanceScheduling
from parameterization.models import EmployeeDepartments

User = get_user_model()


class MaintenanceModelTests(TestCase):
    """Tests para los modelos de mantenimiento"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.department = EmployeeDepartments.objects.create(
            name='Mantenimiento',
            description='Departamento de mantenimiento'
        )
    
    def test_maintenance_creation(self):
        """Test para crear un mantenimiento"""
        maintenance = Maintenance.objects.create(
            name='Mantenimiento Preventivo',
            description='Mantenimiento programado de la excavadora',
            id_responsible_user=self.user,
            maintenance_status='PENDING'
        )
        
        self.assertEqual(maintenance.name, 'Mantenimiento Preventivo')
        self.assertEqual(maintenance.id_responsible_user, self.user)
        self.assertEqual(maintenance.maintenance_status, 'PENDING')
    
    def test_maintenance_str_representation(self):
        """Test para la representación string del mantenimiento"""
        maintenance = Maintenance.objects.create(
            name='Mantenimiento Preventivo',
            id_responsible_user=self.user,
            maintenance_status='PENDING'
        )
        
        self.assertEqual(str(maintenance), 'Mantenimiento Preventivo')
    
    def test_maintenance_request_creation(self):
        """Test para crear una solicitud de mantenimiento"""
        maintenance_request = MaintenanceRequest.objects.create(
            id_responsible_user=self.user,
            description='Solicitud de mantenimiento urgente',
            justification='La máquina presenta fallas en el motor'
        )
        
        self.assertEqual(maintenance_request.id_responsible_user, self.user)
        self.assertEqual(maintenance_request.description, 'Solicitud de mantenimiento urgente')
        self.assertEqual(maintenance_request.justification, 'La máquina presenta fallas en el motor')
    
    def test_maintenance_scheduling_creation(self):
        """Test para crear una programación de mantenimiento"""
        maintenance = Maintenance.objects.create(
            name='Mantenimiento Programado',
            id_responsible_user=self.user,
            maintenance_status='PENDING'
        )
        
        scheduling = MaintenanceScheduling.objects.create(
            id_maintenance=maintenance,
            id_responsible_user=self.user,
            description='Programación para el próximo lunes'
        )
        
        self.assertEqual(scheduling.id_maintenance, maintenance)
        self.assertEqual(scheduling.id_responsible_user, self.user)


class MaintenanceAPITests(APITestCase):
    """Tests para la API de mantenimiento"""
    
    def setUp(self):
        """Configuración inicial para los tests de API"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.maintenance = Maintenance.objects.create(
            name='Mantenimiento Preventivo',
            description='Mantenimiento programado',
            id_responsible_user=self.user,
            maintenance_status='PENDING'
        )
    
    def test_maintenance_list_api(self):
        """Test para listar mantenimientos via API"""
        url = reverse('maintenance-list')
        response = self.client.get(url)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_maintenance_creation_api(self):
        """Test para crear mantenimiento via API"""
        url = reverse('maintenance-list')
        data = {
            'name': 'Nuevo Mantenimiento',
            'description': 'Descripción del nuevo mantenimiento',
            'maintenance_status': 'PENDING'
        }
        
        response = self.client.post(url, data)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_maintenance_request_api(self):
        """Test para la API de solicitudes de mantenimiento"""
        url = reverse('maintenance-request-list')
        data = {
            'description': 'Solicitud de mantenimiento urgente',
            'justification': 'La máquina presenta fallas'
        }
        
        response = self.client.post(url, data)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
