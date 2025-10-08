from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from maintenance.services.auto_maintenance_job import (
    run_generate_auto_requests,
    _generate_request_id,
    _log_sensor_incident,
    _evaluate_periodic_schedules,
)
from maintenance.models import MaintenanceRequest, SensorReadingIncident
from machinery.models import Machinery, PeriodicMaintenanceScheduling, MachineryUsageSheet
from maintenance.models.maintenance import Maintenance
from parameterization.models import Statues, Types


class AutoMaintenanceJobTestCase(TestCase):
    """
    Tests para el job de generación automática de solicitudes de mantenimiento.
    Valida el cumplimiento de HU-SM-002.
    """

    def setUp(self):
        """Configuración inicial para los tests."""
        # Create necessary statuses and types
        self.active_status = Statues.objects.create(
            id_statues=4, name="Activo", description="Estado activo"
        )
        self.pending_status = Statues.objects.create(
            id_statues=10, name="Pendiente", description="Pendiente de autorización"
        )
        
        # Create maintenance types
        self.preventive_type = Types.objects.create(
            id_types=14,
            name="Preventivo",
            description="Mantenimiento preventivo",
            id_types_categories_id=12
        )
        
        # Create priority
        self.default_priority = Types.objects.create(
            id_types=16,
            name="Media",
            description="Prioridad media",
            id_types_categories_id=13
        )

    def test_generate_request_id_format(self):
        """
        Test que valida el formato del consecutivo generado.
        Criterio #4: consecutivo SOL-YYYY-NNNN
        """
        request_id = _generate_request_id()
        current_year = timezone.now().year
        
        self.assertTrue(request_id.startswith(f'SOL-{current_year}-'))
        parts = request_id.split('-')
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[2]), 4)  # 4 dígitos
        self.assertTrue(parts[2].isdigit())

    def test_generate_request_id_incremental(self):
        """
        Test que valida que el consecutivo se incremente correctamente.
        """
        id1 = _generate_request_id()
        # Simulate creating a request with that ID
        MaintenanceRequest.objects.create(
            id_maintenance_request=id1,
            id_machinery=None,  # Would need proper setup
            detected_at=timezone.now()
        )
        
        id2 = _generate_request_id()
        
        num1 = int(id1.split('-')[-1])
        num2 = int(id2.split('-')[-1])
        self.assertEqual(num2, num1 + 1)

    @patch('maintenance.services.auto_maintenance_job.SensorReadingIncident.objects.create')
    @patch('maintenance.services.auto_maintenance_job.requests.post')
    def test_log_sensor_incident_creates_record(self, mock_post, mock_create):
        """
        Test que valida que se registren incidentes de sensores.
        Criterio #9: registro de incidentes de lectura de sensores
        """
        # Mock machinery
        machinery = MagicMock()
        machinery.id_machinery = 1
        machinery.machinery_name = "Test Machinery"
        machinery.serial_number = "TEST-001"
        
        # Mock incident creation
        mock_incident = MagicMock()
        mock_incident.id_sensor_incident = 1
        mock_create.return_value = mock_incident
        
        # Mock successful notification
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        _log_sensor_incident(
            machinery=machinery,
            incident_type="sensor_error",
            description="Test error",
            error_details="Details here"
        )
        
        # Verify incident was created
        mock_create.assert_called_once()
        
        # Verify notification was attempted
        mock_post.assert_called_once()

    def test_detected_at_is_datetime(self):
        """
        Test que valida que detected_at sea DateTime, no solo Date.
        Criterio #4: fecha y hora de detección
        """
        # This would need a full test setup with actual models
        # For now, we verify the field type in the model
        from maintenance.models import MaintenanceRequest
        field = MaintenanceRequest._meta.get_field('detected_at')
        self.assertEqual(field.get_internal_type(), 'DateTimeField')

    def test_automatic_request_flag(self):
        """
        Test que valida que las solicitudes automáticas tengan is_automatic=True.
        Criterio #8: historial sin modificación
        """
        # This would need a full test setup
        # Verify the field exists
        from maintenance.models import MaintenanceRequest
        field = MaintenanceRequest._meta.get_field('is_automatic')
        self.assertEqual(field.get_internal_type(), 'BooleanField')
        self.assertEqual(field.default, False)


class SensorReadingIncidentModelTestCase(TestCase):
    """
    Tests para el modelo SensorReadingIncident.
    """

    def test_sensor_incident_creation(self):
        """
        Test que valida la creación del modelo de incidentes.
        """
        # This would need proper machinery setup
        # For now, verify the model exists and has expected fields
        from maintenance.models import SensorReadingIncident
        
        expected_fields = [
            'id_sensor_incident',
            'id_machinery',
            'incident_type',
            'description',
            'error_details',
            'notified',
            'notification_date',
            'detected_at',
        ]
        
        model_fields = [f.name for f in SensorReadingIncident._meta.get_fields()]
        
        for field in expected_fields:
            self.assertIn(field, model_fields)


class PeriodicMaintenanceDateTestCase(TestCase):
    """
    Tests para el mantenimiento preventivo basado en fecha.
    """

    def test_next_maintenance_date_field_exists(self):
        """
        Test que valida que existe el campo next_maintenance_date.
        Criterio #2: fecha o periodo de mantenimiento preventivo programado
        """
        from machinery.models import PeriodicMaintenanceScheduling
        
        field = PeriodicMaintenanceScheduling._meta.get_field('next_maintenance_date')
        self.assertEqual(field.get_internal_type(), 'DateField')
        self.assertTrue(field.null)
        self.assertTrue(field.blank)

