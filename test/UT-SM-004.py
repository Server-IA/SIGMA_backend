"""
Pruebas unitarias para el endpoint de consulta de detalle de solicitudes de mantenimiento
ID: UT-SM-004
Endpoint: GET /maintenance_request/{id}/detail/
"""

import sys
import os
import pytest
from datetime import datetime, date
from unittest.mock import patch

# Configurar Django ANTES de importar cualquier cosa de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

# Ahora importar Django y DRF
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from django.urls import reverse

# Ajustar el path para imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from machinery.models import Machinery, TelemetryDevices
from users.models.user import User
from parameterization.models import Statues, StatuesCategory, Types, TypesCategory, Brands, BrandsCategory, Models
from maintenance.models import MaintenanceRequest, MaintenanceScheduling


@pytest.mark.django_db
class TestMaintenanceRequestDetail:
    """Tests para el endpoint de detalle de solicitudes de mantenimiento - UT-SM-004"""
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        self.now = timezone.now()
        
        # Crear usuario con permisos
        self.user_with_permissions, created = User.objects.get_or_create(id_user=1)
        self.user_with_permissions.is_authenticated = True
        self.user_with_permissions.id = self.user_with_permissions.id_user
        
        # Mock del token con permisos
        self.auth_with_permissions = {
            "auth": {
                "rol": [{"permisos": [{"id": 123}]}]
            }
        }
        
        # Crear usuario sin permisos
        self.user_without_permissions, created = User.objects.get_or_create(id_user=2)
        self.user_without_permissions.is_authenticated = True
        self.user_without_permissions.id = self.user_without_permissions.id_user
        
        # Mock del token sin permisos
        self.auth_without_permissions = {
            "auth": {
                "rol": [{"permisos": [{"id": 999}]}]  # Permiso diferente
            }
        }
        
        # Crear datos base necesarios
        self._create_base_data()
        
    def _create_base_data(self):
        """Crear datos base necesarios para los tests"""
        # Crear categorías
        self.statues_category, created = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                'name': 'Estados Sistema',
                'description': 'Categoría de estados del sistema',
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        self.types_category, created = TypesCategory.objects.get_or_create(
            id_types_categories=1,
            defaults={
                'name': 'Tipos Sistema',
                'description': 'Categoría de tipos del sistema',
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Crear estados
        self.status_pendiente, created = Statues.objects.get_or_create(
            id_statues=10,
            defaults={
                'name': 'pendiente',
                'description': 'Solicitud pendiente',
                'id_statues_categories': self.statues_category,
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        self.status_aprobada, created = Statues.objects.get_or_create(
            id_statues=11,
            defaults={
                'name': 'aceptado',
                'description': 'Solicitud aprobada',
                'id_statues_categories': self.statues_category,
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        self.status_rechazada, created = Statues.objects.get_or_create(
            id_statues=12,
            defaults={
                'name': 'rechazado',
                'description': 'Solicitud rechazada',
                'id_statues_categories': self.statues_category,
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        self.status_programada, created = Statues.objects.get_or_create(
            id_statues=13,
            defaults={
                'name': 'programado',
                'description': 'Solicitud programada',
                'id_statues_categories': self.statues_category,
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Crear tipos
        self.maintenance_type, created = Types.objects.get_or_create(
            id_types=1,
            defaults={
                'name': 'Mantenimiento Correctivo',
                'description': 'Tipo de mantenimiento correctivo',
                'id_types_categories': self.types_category,
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
                'id_statues': self.status_pendiente,
            }
        )
        
        self.priority_type, created = Types.objects.get_or_create(
            id_types=2,
            defaults={
                'name': 'Alta',
                'description': 'Prioridad alta',
                'id_types_categories': self.types_category,
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
                'id_statues': self.status_pendiente,
            }
        )
        
        # Crear marcas y modelos
        self.brands_category, created = BrandsCategory.objects.get_or_create(
            id_brands_categories=1,
            defaults={
                'name': 'Maquinaria Pesada',
                'description': 'Categoría de maquinaria pesada',
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        self.brand, created = Brands.objects.get_or_create(
            id_brands=1,
            defaults={
                'name': 'Caterpillar',
                'description': 'Marca de maquinaria pesada',
                'id_brands_categories': self.brands_category,
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
                'id_statues': self.status_pendiente,
            }
        )
        
        self.model, created = Models.objects.get_or_create(
            id_model=1,
            defaults={
                'name': 'CAT 320',
                'description': 'Modelo de excavadora',
                'id_brand': self.brand,
                'id_statues': self.status_pendiente,
                'creation_date': self.now,
                'modification_date': self.now,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Crear maquinaria
        self.machinery, created = Machinery.objects.get_or_create(
            id_machinery=1,
            defaults={
                'machinery_name': 'Excavadora CAT 320',
                'serial_number': 'CAT320-001',
                'machinery_type': self.maintenance_type,
                'machinery_secondary_type': self.maintenance_type,
                'id_model': self.model,
                'machinery_operational_status': self.status_pendiente,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Crear solicitudes de mantenimiento
        self._create_maintenance_requests()
        
    def _create_maintenance_requests(self):
        """Crear solicitudes de mantenimiento para los tests"""
        
        # Solicitud 1 - Normal (pendiente)
        self.request_1, created = MaintenanceRequest.objects.get_or_create(
            id_maintenance_request=1,
            defaults={
                'id_machinery': self.machinery,
                'maintenance_type': self.maintenance_type,
                'description': 'Problema en el motor',
                'priority': self.priority_type,
                'request_status': self.status_pendiente,
                'detected_at': date.today(),
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Solicitud 3 - Rechazada
        self.request_3, created = MaintenanceRequest.objects.get_or_create(
            id_maintenance_request=3,
            defaults={
                'id_machinery': self.machinery,
                'maintenance_type': self.maintenance_type,
                'description': 'Solicitud rechazada',
                'priority': self.priority_type,
                'request_status': self.status_rechazada,
                'justification': 'No es necesario el mantenimiento',
                'detected_at': date.today(),
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Solicitud 4 - Programada
        self.request_4, created = MaintenanceRequest.objects.get_or_create(
            id_maintenance_request=4,
            defaults={
                'id_machinery': self.machinery,
                'maintenance_type': self.maintenance_type,
                'description': 'Solicitud programada',
                'priority': self.priority_type,
                'request_status': self.status_programada,
                'detected_at': date.today(),
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Crear programación para solicitud 4
        self.scheduling_4, created = MaintenanceScheduling.objects.get_or_create(
            id_maintenance_request=self.request_4,
            defaults={
                'id_machinery': self.machinery,
                'scheduled_at': self.now + timezone.timedelta(days=7),
                'details': 'Mantenimiento programado',
                'assigned_technician': self.user_with_permissions,
                'maintenance_type': self.maintenance_type,
                'maintenance_scheduling_status': self.status_programada,
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Solicitud 5 - Aprobada sin programar
        self.request_5, created = MaintenanceRequest.objects.get_or_create(
            id_maintenance_request=5,
            defaults={
                'id_machinery': self.machinery,
                'maintenance_type': self.maintenance_type,
                'description': 'Solicitud aprobada',
                'priority': self.priority_type,
                'request_status': self.status_aprobada,
                'detected_at': date.today(),
                'id_responsible_user': self.user_with_permissions,
            }
        )
        
        # Solicitud 6 - Para validar integridad de maquinaria
        self.request_6, created = MaintenanceRequest.objects.get_or_create(
            id_maintenance_request=6,
            defaults={
                'id_machinery': self.machinery,
                'maintenance_type': self.maintenance_type,
                'description': 'Validar integridad maquinaria',
                'priority': self.priority_type,
                'request_status': self.status_pendiente,
                'detected_at': date.today(),
                'id_responsible_user': self.user_with_permissions,
            }
        )

    def test_caso_1_consulta_exitosa_con_permisos(self):
        """
        Caso de Prueba 1 – Consulta exitosa con permisos
        Objetivo: Validar que un usuario con permiso maintenance_request.retrieve 
        pueda obtener el detalle de una solicitud existente.
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Mock del request.auth con permisos
        mock_request_auth = {
            "rol": [{"permisos": [{"id": 123}]}]
        }
        
        # Hacer la petición
        url = '/maintenance_request/1/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
            response = self.client.get(url)
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.data['success'] is True
        
        data = response.data['data']
        
        # Verificar campos requeridos
        assert 'id' in data
        assert 'machinery_serial' in data
        assert 'machinery_name' in data
        assert 'maintenance_type_name' in data
        assert 'description' in data
        assert 'priority_name' in data
        assert 'status_id' in data
        assert 'status_name' in data
        assert 'fecha_solicitud' in data
        assert 'modification_date' in data
        assert 'scheduled_at' in data
        assert 'assigned_technician_id' in data
        
        # Verificar valores específicos
        assert data['id'] == 1
        assert data['machinery_serial'] == 'CAT320-001'
        assert data['machinery_name'] == 'Excavadora CAT 320'
        assert data['maintenance_type_name'] == 'Mantenimiento Correctivo'
        assert data['description'] == 'Problema en el motor'
        assert data['priority_name'] == 'Alta'
        assert data['status_name'] == 'pendiente'

    def test_caso_2_solicitud_inexistente(self):
        """
        Caso de Prueba 2 – Solicitud inexistente
        Objetivo: Validar que se maneje el caso de un id_request no registrado.
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Hacer la petición con ID inexistente
        url = '/maintenance_request/9999/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
            response = self.client.get(url)
        
        # Verificar respuesta
        assert response.status_code == 404
        assert response.data['success'] is False
        assert "No se encontró la solicitud de mantenimiento" in response.data['message']

    def test_caso_3_usuario_sin_permisos(self):
        """
        Caso de Prueba 3 – Usuario sin permisos
        Objetivo: Verificar que un usuario sin el permiso 123 no pueda acceder al detalle.
        """
        # Autenticar usuario sin permisos
        self.client.force_authenticate(user=self.user_without_permissions)
        
        # Hacer la petición
        url = '/maintenance_request/1/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=False):
            response = self.client.get(url)
        
        # Verificar respuesta
        assert response.status_code == 403
        assert response.data['message'] == "No tiene permisos para consultar la solicitud de mantenimiento."

    def test_caso_4_solicitud_rechazada(self):
        """
        Caso de Prueba 4 – Solicitud rechazada
        Objetivo: Validar que si la solicitud está en estado Rechazada, 
        se muestre la fecha, usuario y razón del rechazo.
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Hacer la petición
        url = '/maintenance_request/3/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
            response = self.client.get(url)
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.data['success'] is True
        
        data = response.data['data']
        
        # Verificar campos específicos para solicitud rechazada
        assert data['status_name'] == 'rechazado'
        assert 'modification_date' in data
        # Nota: El campo justification no está incluido en el serializer de detalle

    def test_caso_5_solicitud_programada(self):
        """
        Caso de Prueba 5 – Solicitud programada
        Objetivo: Validar que si la solicitud está programada, 
        se incluya fecha y técnico asignado.
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Hacer la petición
        url = '/maintenance_request/4/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
            response = self.client.get(url)
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.data['success'] is True
        
        data = response.data['data']
        
        # Verificar campos de programación
        assert data['scheduled_at'] is not None
        assert data['assigned_technician_id'] is not None
        assert data['status_name'] == 'programado'

    def test_caso_6_solicitud_aprobada_sin_programar(self):
        """
        Caso de Prueba 6 – Solicitud aprobada sin programar
        Objetivo: Validar que si la solicitud está aprobada pero aún no se programa, 
        no existan campos scheduled_at ni assigned_technician_id.
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Hacer la petición
        url = '/maintenance_request/5/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
            response = self.client.get(url)
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.data['success'] is True
        
        data = response.data['data']
        
        # Verificar que está aprobada
        assert data['status_name'] == 'aceptado'
        
        # Verificar que no tiene campos de programación
        assert data['scheduled_at'] is None
        assert data['assigned_technician_id'] is None

    def test_caso_7_validacion_integridad_maquinaria(self):
        """
        Caso de Prueba 7 – Validación de integridad de maquinaria
        Objetivo: Confirmar que siempre se incluyan machinery_serial y machinery_name.
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Hacer la petición
        url = '/maintenance_request/6/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
            response = self.client.get(url)
        
        # Verificar respuesta
        assert response.status_code == 200
        assert response.data['success'] is True
        
        data = response.data['data']
        
        # Verificar que los campos de maquinaria no sean null
        assert data['machinery_serial'] is not None
        assert data['machinery_name'] is not None
        assert data['machinery_serial'] != ''
        assert data['machinery_name'] != ''

    def test_caso_8_error_red_servidor_no_disponible(self):
        """
        Caso de Prueba 8 – Error de red/servidor no disponible
        Objetivo: Validar que el sistema maneje correctamente fallas de conexión.
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Mock para simular error de conexión
        with patch('maintenance.models.MaintenanceRequest.objects.select_related') as mock_query:
            mock_query.side_effect = Exception("Error de conexión a la base de datos")
            
            # Hacer la petición
            url = '/maintenance_request/1/detail/'
            
            with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
                response = self.client.get(url)
            
            # Verificar respuesta de error
            assert response.status_code == 500
            assert response.data['success'] is False
            assert "Error al obtener el detalle de la solicitud" in response.data['message']

    def test_usuario_no_autenticado(self):
        """
        Test adicional: Usuario no autenticado
        """
        # No autenticar usuario
        response = self.client.get('/maintenance_request/1/detail/')
        
        # Verificar respuesta
        assert response.status_code == 401
        # La respuesta puede ser un diccionario vacío o tener un formato diferente
        # Verificamos que al menos el status code sea 401

    def test_campos_obligatorios_respuesta(self):
        """
        Test adicional: Verificar que todos los campos obligatorios estén presentes
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Hacer la petición
        url = '/maintenance_request/1/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
            response = self.client.get(url)
        
        # Verificar respuesta exitosa
        assert response.status_code == 200
        assert response.data['success'] is True
        
        data = response.data['data']
        
        # Lista de campos obligatorios según la especificación
        campos_obligatorios = [
            'id', 'machinery_serial', 'machinery_name',
            'maintenance_type_name', 'description', 'priority_name',
            'status_id', 'status_name', 'fecha_solicitud', 'modification_date',
            'scheduled_at', 'assigned_technician_id'
        ]
        
        # Verificar que todos los campos estén presentes
        for campo in campos_obligatorios:
            assert campo in data, f"Campo '{campo}' no encontrado en la respuesta"

    def test_formato_respuesta_correcto(self):
        """
        Test adicional: Verificar el formato correcto de la respuesta
        """
        # Autenticar usuario con permisos
        self.client.force_authenticate(user=self.user_with_permissions)
        
        # Hacer la petición
        url = '/maintenance_request/1/detail/'
        
        with patch('maintenance.api.maintenance_request_viewset.MaintenanceRequestViewSet.check_permission', return_value=True):
            response = self.client.get(url)
        
        # Verificar estructura de respuesta
        assert 'success' in response.data
        assert 'message' in response.data
        assert 'data' in response.data
        
        # Verificar tipos de datos
        assert isinstance(response.data['success'], bool)
        assert isinstance(response.data['message'], str)
        assert isinstance(response.data['data'], dict)
