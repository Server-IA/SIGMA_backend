from django.contrib import admin
from maintenance.models import SensorReadingIncident, MaintenanceRequest


@admin.register(SensorReadingIncident)
class SensorReadingIncidentAdmin(admin.ModelAdmin):
    """
    Admin interface para incidentes de lectura de sensores.
    """
    list_display = (
        'id_sensor_incident',
        'id_machinery',
        'incident_type',
        'detected_at',
        'notified',
        'notification_date',
    )
    list_filter = ('incident_type', 'notified', 'detected_at')
    search_fields = ('description', 'error_details', 'id_machinery__machinery_name')
    readonly_fields = (
        'id_sensor_incident',
        'detected_at',
        'registration_date',
        'modification_date',
    )
    ordering = ('-detected_at',)


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    """
    Admin interface para solicitudes de mantenimiento.
    """
    list_display = (
        'id_maintenance_request',
        'id_machinery',
        'maintenance_type',
        'priority',
        'request_status',
        'is_automatic',
        'detected_at',
    )
    list_filter = ('is_automatic', 'request_status', 'maintenance_type', 'priority')
    search_fields = ('id_maintenance_request', 'description', 'id_machinery__machinery_name')
    readonly_fields = (
        'id_maintenance_request',
        'registration_date',
        'modification_date',
    )
    
    def has_delete_permission(self, request, obj=None):
        """
        No permitir eliminación de solicitudes automáticas.
        Criterio #8 HU-SM-002.
        """
        if obj and obj.is_automatic:
            return False
        return super().has_delete_permission(request, obj)
    
    def has_change_permission(self, request, obj=None):
        """
        No permitir modificación de solicitudes automáticas.
        Criterio #8 HU-SM-002.
        """
        if obj and obj.is_automatic:
            return False
        return super().has_change_permission(request, obj)

