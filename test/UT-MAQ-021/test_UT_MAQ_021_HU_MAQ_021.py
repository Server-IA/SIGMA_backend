"""
Pruebas unitarias para creación y actualización de umbrales de tolerancia de maquinaria
ID: UT-MAQ-021

Historia de Usuario: Como administrador, quiero configurar y actualizar umbrales de tolerancia
para los parámetros de maquinaria, fallos OBD y tipos de eventos, para poder monitorear
el estado operativo de las máquinas y recibir alertas cuando se excedan los límites establecidos.

Endpoints bajo prueba:
- POST /tolerance-thresholds/create/ - Crear umbrales de tolerancia
- PATCH /tolerance-thresholds/update/?machinery_id={id} - Actualizar umbrales de tolerancia

Permisos requeridos:
- 164: machinery_tolerance_thresholds.create - Crear umbrales
- 166: machinery_tolerance_thresholds.update - Actualizar umbrales
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from django.utils import timezone
from rest_framework.test import APIClient

from machinery.models import (
    Machinery,
    ToleranceThresholds,
    OBDFaultMachinery,
    EventTypeMachinery,
    Parameters,
    OBD_Faults,
    EventTypes,
    TelemetryDevices
)
from maintenance.models import Maintenance
from users.models import User
from parameterization.models import (
    Statues,
    StatuesCategory,
    Types,
    TypesCategory,
    Models,
    Brands,
    BrandsCategory
)


@pytest.mark.django_db
class TestToleranceThresholdsEndpoints:
    """Pruebas para los endpoints de umbrales de tolerancia"""
    
    create_endpoint = "/tolerance-thresholds/create/"
    update_endpoint_template = "/tolerance-thresholds/update/?machinery_id={}"
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        
        # Crear usuario responsable
        self.responsible_user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_create_permission = self._token_with_permissions([164])
        self.token_with_update_permission = self._token_with_permissions([166])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Inicializar parametrización base
        self._bootstrap_parametrization()
        
        # Crear parámetros de prueba
        self._create_test_parameters()
        
        # Crear fallos OBD de prueba
        self._create_test_obd_faults()
        
        # Crear tipos de eventos de prueba
        self._create_test_event_types()
        
        # Crear mantenimientos de prueba
        self._create_test_maintenances()
        
        # Crear maquinarias de prueba
        self._create_test_machineries()
        
        # Limpiar umbrales previos
        EventTypeMachinery.objects.all().delete()
        OBDFaultMachinery.objects.all().delete()
        ToleranceThresholds.objects.all().delete()
    
    # ==================== HELPERS ====================
    
    def _ensure_user(self, user_id: int) -> User:
        """Crea o recupera un usuario para pruebas"""
        user, created = User.objects.get_or_create(
            id_user=user_id
        )
        user.id = user.id_user
        user.is_authenticated = True
        return user
    
    def _token_with_permissions(self, permission_ids):
        """Genera payload de token con permisos específicos"""
        perms = [{"id": perm_id} for perm_id in permission_ids]
        return {
            "roles": [{"permisos": perms, "permissions": perms}],
            "permisos": perms,
            "permissions": perms,
        }
    
    def _bootstrap_parametrization(self):
        """Inicializa datos de parametrización necesarios"""
        # Categoría de estados generales
        self.statues_category_general = StatuesCategory.objects.create(
            id_statues_categories=1,
            name="Estados generales",
            description="Estados del sistema",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Estados generales
        self.status_active = Statues.objects.create(
            id_statues=1,
            name="Activo",
            description="Estado activo",
            id_statues_categories=self.statues_category_general,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Categoría de tipos de maquinaria
        self.machinery_types_category = TypesCategory.objects.create(
            id_types_categories=1,
            name="Tipos de maquinaria",
            description="Categoría de tipos de maquinaria",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Tipo de maquinaria
        self.machinery_type = Types.objects.create(
            id_types=1,
            name="Tractor",
            description="Tipo tractor",
            id_types_categories=self.machinery_types_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
            id_statues=self.status_active,
        )
        
        # Categoría de marcas
        self.brands_category = BrandsCategory.objects.create(
            id_brands_categories=1,
            name="Maquinaria Agrícola",
            description="Categoría de marcas de maquinaria agrícola",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Marca
        self.brand = Brands.objects.create(
            id_brands=1,
            name="John Deere",
            description="Marca John Deere",
            id_brands_categories=self.brands_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
            id_statues=self.status_active,
        )
        
        # Modelo
        self.model = Models.objects.create(
            id_model=1,
            name="6155M",
            description="Modelo 6155M",
            id_brand=self.brand,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
            id_statues=self.status_active,
        )
    
    def _create_test_parameters(self):
        """Crea parámetros de prueba"""
        # Parámetro 7: Temperatura del motor (rango: -60 a 127)
        self.parameter_7 = Parameters.objects.create(
            id=7,
            parameter_name="Temperatura del motor",
            avl_id_parameter=7,
            description="Temperatura del motor en grados Celsius",
            minimum_range=-60,
            maximum_range=127,
            unit="°C"
        )
        
        # Parámetro 12: RPM del motor (rango: 300 a 30000)
        self.parameter_12 = Parameters.objects.create(
            id=12,
            parameter_name="RPM del motor",
            avl_id_parameter=12,
            description="Revoluciones por minuto del motor",
            minimum_range=300,
            maximum_range=30000,
            unit="RPM"
        )
        
        # Parámetro 17: Valor G (para eventos)
        self.parameter_17 = Parameters.objects.create(
            id=17,
            parameter_name="Valor G",
            avl_id_parameter=17,
            description="Aceleración en G",
            minimum_range=0,
            maximum_range=500,
            unit="G"
        )
        
        # Parámetros no permitidos (1, 2, 4, 5, 13, 16, 17)
        self.parameter_1 = Parameters.objects.create(
            id=1,
            parameter_name="Parámetro no permitido 1",
            avl_id_parameter=1,
            description="Parámetro no permitido",
            minimum_range=0,
            maximum_range=100,
            unit="unit"
        )
    
    def _create_test_obd_faults(self):
        """Crea fallos OBD de prueba"""
        self.obd_fault_1 = OBD_Faults.objects.create(
            id_obd_fault=1,
            code="P0001",
            description="Fallo OBD 1"
        )
        
        self.obd_fault_3 = OBD_Faults.objects.create(
            id_obd_fault=3,
            code="P0003",
            description="Fallo OBD 3"
        )
    
    def _create_test_event_types(self):
        """Crea tipos de eventos de prueba"""
        self.event_type_1 = EventTypes.objects.create(
            id_event_type=1,
            name="Frenado brusco"
        )
        
        self.event_type_3 = EventTypes.objects.create(
            id_event_type=3,
            name="Aceleración brusca"
        )
    
    def _create_test_maintenances(self):
        """Crea mantenimientos de prueba"""
        # Crear tipo de mantenimiento
        maintenance_types_category = TypesCategory.objects.create(
            id_types_categories=2,
            name="Tipos de mantenimiento",
            description="Categoría de tipos de mantenimiento",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        maintenance_type = Types.objects.create(
            id_types=2,
            name="Preventivo",
            description="Tipo preventivo",
            id_types_categories=maintenance_types_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
            id_statues=self.status_active,
        )
        
        self.maintenance_1 = Maintenance.objects.create(
            id_maintenance=1,
            name="Mantenimiento preventivo",
            description="Mantenimiento preventivo general",
            maintenance_type=maintenance_type,
            maintenance_status=self.status_active,
            id_responsible_user=self.responsible_user
        )
        
        self.maintenance_2 = Maintenance.objects.create(
            id_maintenance=2,
            name="Mantenimiento correctivo",
            description="Mantenimiento correctivo",
            maintenance_type=maintenance_type,
            maintenance_status=self.status_active,
            id_responsible_user=self.responsible_user
        )
        
        self.maintenance_3 = Maintenance.objects.create(
            id_maintenance=3,
            name="Mantenimiento predictivo",
            description="Mantenimiento predictivo",
            maintenance_type=maintenance_type,
            maintenance_status=self.status_active,
            id_responsible_user=self.responsible_user
        )
    
    def _create_test_machineries(self):
        """Crea maquinarias de prueba"""
        # Maquinarias para pruebas de creación (8, 9, 10, 11)
        for i in [8, 9, 10, 11]:
            Machinery.objects.create(
                id_machinery=i,
                machinery_name=f"Tractor Test {i}",
                serial_number=f"SN-TEST-{i}",
                machinery_type=self.machinery_type,
                machinery_secondary_type=self.machinery_type,
                id_model=self.model,
                machinery_operational_status=self.status_active,
                id_responsible_user=self.responsible_user,
                registration_date=self.now.date(),
                modification_date=self.now.date()
            )
        
        # Maquinaria para prueba de actualización (12)
        Machinery.objects.create(
            id_machinery=12,
            machinery_name="Tractor Test 12",
            serial_number="SN-TEST-12",
            machinery_type=self.machinery_type,
            machinery_secondary_type=self.machinery_type,
            id_model=self.model,
            machinery_operational_status=self.status_active,
            id_responsible_user=self.responsible_user,
            registration_date=self.now.date(),
            modification_date=self.now.date()
        )
    
    def _get_valid_create_payload(self, machinery_id=8):
        """Retorna un payload válido para crear umbrales"""
        return {
            "id_machinery": machinery_id,
            "tolerance_thresholds": [
                {
                    "id_parameter": 7,
                    "minimum_threshold": -20.5,
                    "maximum_threshold": 80.2,
                    "id_maintenance": 1,
                    "alert_enabled": True
                },
                {
                    "id_parameter": 12,
                    "minimum_threshold": 300,
                    "maximum_threshold": 30000,
                    "id_maintenance": 1,
                    "alert_enabled": True
                }
            ],
            "obd_fault_machinery": [
                {
                    "id_obd_fault": 1,
                    "alert_enabled": True,
                    "id_maintenance": 2
                },
                {
                    "id_obd_fault": 3,
                    "alert_enabled": False,
                    "id_maintenance": None
                }
            ],
            "event_type_machinery": [
                {
                    "id_event_type": 1,
                    "threshold": 25.5,
                    "alert_enabled": True,
                    "id_maintenance": 3
                },
                {
                    "id_event_type": 3,
                    "threshold": 200,
                    "alert_enabled": False,
                    "id_maintenance": None
                }
            ]
        }
    
    def _get_valid_update_payload(self):
        """Retorna un payload válido para actualizar umbrales"""
        return {
            "tolerance_thresholds": [
                {
                    "id_parameter": 7,
                    "minimum_threshold": -10,
                    "maximum_threshold": 90,
                    "id_maintenance": 1,
                    "alert_enabled": True
                },
                {
                    "id_parameter": 12,
                    "minimum_threshold": 400,
                    "maximum_threshold": 29000,
                    "id_maintenance": 1,
                    "alert_enabled": True
                }
            ],
            "obd_fault_machinery": [
                {
                    "id_obd_fault": 1,
                    "alert_enabled": True,
                    "id_maintenance": 2
                },
                {
                    "id_obd_fault": 3,
                    "alert_enabled": False,
                    "id_maintenance": None
                }
            ],
            "event_type_machinery": [
                {
                    "id_event_type": 1,
                    "threshold": 30,
                    "alert_enabled": True,
                    "id_maintenance": 3
                },
                {
                    "id_event_type": 3,
                    "threshold": 200,
                    "alert_enabled": False,
                    "id_maintenance": None
                }
            ]
        }
    
    def _create_existing_thresholds(self, machinery_id=8):
        """Crea umbrales existentes para una maquinaria"""
        machinery = Machinery.objects.get(id_machinery=machinery_id)
        
        ToleranceThresholds.objects.create(
            id_machinery=machinery,
            id_parameter=self.parameter_7,
            minimum_threshold=-20.5,
            maximum_threshold=80.2,
            id_maintenance=self.maintenance_1,
            alert_enabled=True
        )
    
    # ==================== PRUEBAS DE CREACIÓN ====================
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_create_success(self, mock_audit):
        """
        UT-MAQ-021: 201 Created – Creación exitosa (camino feliz)
        
        Verificar que el endpoint permite registrar correctamente los umbrales de tolerancia
        para una maquinaria cuando todos los datos son válidos y la maquinaria no posee
        configuraciones previas.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        payload = self._get_valid_create_payload(machinery_id=8)
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_create_permission
        
        # Act
        response = self.client.post(
            self.create_endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.data}"
        assert response.data['success'] is True
        assert response.data['message'] == "Umbrales de tolerancia creados exitosamente"
        
        # Verificar en base de datos
        assert ToleranceThresholds.objects.filter(id_machinery=8).count() == 2
        assert OBDFaultMachinery.objects.filter(id_machinery=8).count() == 2
        assert EventTypeMachinery.objects.filter(id_machinery=8).count() == 2
        
        print(f"✅ UT-MAQ-021: APROBADO - Umbrales creados exitosamente para maquinaria 8")
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_1_conflict_existing_thresholds(self, mock_audit):
        """
        UT-MAQ-021.1: 409 Conflict – Ya existen umbrales para la maquinaria
        
        Verificar que el endpoint rechaza la creación si la maquinaria ya posee
        umbrales configurados.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        # Crear umbrales existentes para maquinaria 8
        self._create_existing_thresholds(machinery_id=8)
        
        payload = self._get_valid_create_payload(machinery_id=8)
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_create_permission
        
        # Act
        response = self.client.post(
            self.create_endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.data}"
        assert response.data['success'] is False
        assert response.data['message'] == "Ya existen umbrales de tolerancia previas para esta maquinaria"
        
        print(f"✅ UT-MAQ-021.1: APROBADO - Conflicto detectado correctamente")
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_2_invalid_parameter(self, mock_audit):
        """
        UT-MAQ-021.2: 400 Bad Request – Parámetro no permitido
        
        Verificar que no se permite usar parámetros con IDs no válidos (1, 2, 4, 5, 13, 16, 17).
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        payload = {
            "id_machinery": 9,
            "tolerance_thresholds": [
                {
                    "id_parameter": 1,
                    "minimum_threshold": 0,
                    "maximum_threshold": 1,
                    "id_maintenance": 1,
                    "alert_enabled": True
                }
            ]
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_create_permission
        
        # Act
        response = self.client.post(
            self.create_endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.data}"
        assert response.data['success'] is False
        assert 'errors' in response.data
        assert 'tolerance_thresholds' in response.data['errors']
        
        error_message = str(response.data['errors']['tolerance_thresholds'])
        assert 'parámetro con ID 1' in error_message or 'no puede ser utilizado' in error_message
        
        print(f"✅ UT-MAQ-021.2: APROBADO - Parámetro no permitido rechazado correctamente")
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_3_values_out_of_range(self, mock_audit):
        """
        UT-MAQ-021.3: 400 Bad Request – Valores fuera de rango
        
        Verificar que el sistema valida que los valores mínimos y máximos estén dentro
        del rango permitido del parámetro.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        payload = {
            "id_machinery": 10,
            "tolerance_thresholds": [
                {
                    "id_parameter": 7,
                    "minimum_threshold": -900.5,
                    "maximum_threshold": 80000.2,
                    "id_maintenance": 1,
                    "alert_enabled": True
                }
            ]
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_create_permission
        
        # Act
        response = self.client.post(
            self.create_endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.data}"
        assert response.data['success'] is False
        assert 'errors' in response.data
        assert 'tolerance_thresholds' in response.data['errors']
        
        error_message = str(response.data['errors']['tolerance_thresholds'])
        # El validador retorna el primer error encontrado
        assert ('minimum_threshold' in error_message or '-900.5' in error_message or 
                'maximum_threshold' in error_message or '80000.2' in error_message)
        
        print(f"✅ UT-MAQ-021.3: APROBADO - Valores fuera de rango rechazados correctamente")
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_4_minimum_greater_than_maximum(self, mock_audit):
        """
        UT-MAQ-021.4: 400 Bad Request – Valor mínimo mayor que máximo
        
        Verificar que el sistema impide registrar umbrales donde minimum_threshold > maximum_threshold.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        payload = {
            "id_machinery": 11,
            "tolerance_thresholds": [
                {
                    "id_parameter": 7,
                    "minimum_threshold": 100,
                    "maximum_threshold": 60,
                    "id_maintenance": 1,
                    "alert_enabled": True
                }
            ]
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_create_permission
        
        # Act
        response = self.client.post(
            self.create_endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.data}"
        assert response.data['success'] is False
        assert 'errors' in response.data
        assert 'tolerance_thresholds' in response.data['errors']
        
        error_message = str(response.data['errors']['tolerance_thresholds'])
        assert 'minimum_threshold' in error_message and 'maximum_threshold' in error_message
        assert '100' in error_message and '60' in error_message
        
        print(f"✅ UT-MAQ-021.4: APROBADO - Mínimo mayor que máximo rechazado correctamente")
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_5_missing_required_fields(self, mock_audit):
        """
        UT-MAQ-021.5: 400 Bad Request – Campos obligatorios faltantes
        
        Verificar que se retorna error cuando faltan los campos obligatorios
        id_machinery o tolerance_thresholds.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        payload = {
            "tolerance_thresholds": []
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_create_permission
        
        # Act
        response = self.client.post(
            self.create_endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.data}"
        assert response.data['success'] is False
        assert 'errors' in response.data
        assert 'id_machinery' in response.data['errors']
        
        print(f"✅ UT-MAQ-021.5: APROBADO - Campos obligatorios validados correctamente")
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_6_forbidden_no_permission(self, mock_audit):
        """
        UT-MAQ-021.6: 403 Forbidden – Usuario sin permiso de creación
        
        Verificar que el endpoint rechaza solicitudes de usuarios sin el permiso 164.
        """
        # Arrange
        mock_audit.return_value.create = MagicMock()
        
        payload = self._get_valid_create_payload(machinery_id=8)
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_without_permission
        
        # Act
        response = self.client.post(
            self.create_endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.data}"
        
        print(f"✅ UT-MAQ-021.6: APROBADO - Permisos validados correctamente")
    
    # ==================== PRUEBAS DE ACTUALIZACIÓN ====================
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_7_update_success(self, mock_audit):
        """
        UT-MAQ-021.7: 200 OK – Actualización exitosa (camino feliz)
        
        Verificar que el endpoint PATCH actualiza correctamente los umbrales existentes.
        """
        # Arrange
        mock_audit.return_value.update = MagicMock()
        
        # Crear umbrales existentes para maquinaria 12
        self._create_existing_thresholds(machinery_id=12)
        
        payload = self._get_valid_update_payload()
        endpoint = self.update_endpoint_template.format(12)
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_update_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        assert response.data['success'] is True
        assert response.data['message'] == "Umbrales de tolerancia actualizados exitosamente"
        
        # Verificar en base de datos que se actualizaron
        thresholds = ToleranceThresholds.objects.filter(id_machinery=12)
        assert thresholds.count() == 2
        
        print(f"✅ UT-MAQ-021.7: APROBADO - Umbrales actualizados exitosamente")
    
    @patch('machinery.api.machinery_tolerance_thresholds_viewset.AuditClient')
    def test_ut_maq_021_8_update_validation_error(self, mock_audit):
        """
        UT-MAQ-021.8: 400 Bad Request – Error de validación en actualización
        
        Verificar que se devuelven errores de validación al intentar actualizar
        con valores fuera de rango.
        """
        # Arrange
        mock_audit.return_value.update = MagicMock()
        
        # Crear umbrales existentes para maquinaria 12
        self._create_existing_thresholds(machinery_id=12)
        
        payload = {
            "tolerance_thresholds": [
                {
                    "id_parameter": 7,
                    "minimum_threshold": -900.5,
                    "maximum_threshold": 80000.2,
                    "id_maintenance": 1,
                    "alert_enabled": True
                }
            ]
        }
        
        endpoint = self.update_endpoint_template.format(12)
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_update_permission
        
        # Act
        response = self.client.patch(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.data}"
        assert response.data['success'] is False
        assert 'errors' in response.data
        assert 'tolerance_thresholds' in response.data['errors']
        
        error_message = str(response.data['errors']['tolerance_thresholds'])
        # El validador retorna el primer error encontrado
        assert ('minimum_threshold' in error_message or '-900.5' in error_message or 
                'maximum_threshold' in error_message or '80000.2' in error_message)
        
        print(f"✅ UT-MAQ-021.8: APROBADO - Errores de validación en actualización detectados correctamente")


def main():
    """Función principal para ejecutar las pruebas"""
    print("🚀 EJECUTANDO PRUEBAS UT-MAQ-021 - UMBRALES DE TOLERANCIA")
    print("=" * 80)
    
    # Ejecutar pytest
    pytest.main([__file__, '-v', '-s'])


if __name__ == '__main__':
    main()

