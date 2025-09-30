from rest_framework import serializers
from maintenance.models import MaintenanceReport


class MaintenanceReportListSerializer(serializers.ModelSerializer):
    """
    Serializador para listar reportes de mantenimiento con información básica.
    """
    
    # Información del mantenimiento programado
    machinery_serial = serializers.CharField(
        source='id_maintenance_scheduling.id_machinery.serial_number', 
        read_only=True
    )
    machinery_name = serializers.CharField(
        source='id_maintenance_scheduling.id_machinery.machinery_name', 
        read_only=True
    )
    machinery_type = serializers.CharField(
        source='id_maintenance_scheduling.id_machinery.machinery_type.name', 
        read_only=True
    )
    
    # Información del técnico asignado
    assigned_technician_id = serializers.IntegerField(
        source='id_maintenance_scheduling.assigned_technician.id_user', 
        read_only=True
    )
    
    # Información del usuario responsable
    responsible_user_id = serializers.IntegerField(
        source='id_responsible_user.id_user', 
        read_only=True
    )
    
    # Campos calculados
    total_time_minutes = serializers.SerializerMethodField()
    
    def get_total_time_minutes(self, obj):
        """
        Calcula el tiempo total en minutos.
        """
        return (obj.time_invested_hours * 60) + obj.time_invested_minutes

    class Meta:
        model = MaintenanceReport
        fields = [
            'id_maintenance_report',
            'title',
            'description',
            'creation_date',
            'time_invested_hours',
            'time_invested_minutes',
            'total_time_minutes',
            'spare_parts_total_cost',
            'total_cost',
            'machinery_serial',
            'machinery_name',
            'machinery_type',
            'assigned_technician_id',
            'responsible_user_id',
            'registration_date'
        ]
