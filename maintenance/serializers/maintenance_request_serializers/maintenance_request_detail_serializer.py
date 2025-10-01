from rest_framework import serializers
from maintenance.models.maintenance_request import MaintenanceRequest
from maintenance.models.maintenance_scheduling import MaintenanceScheduling


class MaintenanceRequestDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="id_maintenance_request", read_only=True)
    machinery_serial = serializers.CharField(source="id_machinery.serial_number", read_only=True)
    machinery_name = serializers.CharField(source="id_machinery.machinery_name", read_only=True)
    maintenance_type_name = serializers.CharField(source="maintenance_type.name", read_only=True)
    fecha_solicitud = serializers.DateTimeField(source="registration_date", read_only=True)
    priority_name = serializers.CharField(source="priority.name", read_only=True)
    status_name = serializers.CharField(source="request_status.name", read_only=True)
    status_id = serializers.IntegerField(source="request_status.id_statues", read_only=True)
    
    scheduled_at = serializers.SerializerMethodField()
    assigned_technician_id = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "machinery_serial",
            "machinery_name",
            "maintenance_type_name",
            "description",
            "priority_name",
            "status_id",
            "status_name",
            "fecha_solicitud",
            "response_date",
            "scheduled_at",
            "assigned_technician_id",
            "justification",
            "id_response_user",
        ]

    def get_scheduled_at(self, obj):
        try:
            scheduling = MaintenanceScheduling.objects.get(id_maintenance_request=obj)
            return scheduling.scheduled_at
        except MaintenanceScheduling.DoesNotExist:
            return None

    def get_assigned_technician_id(self, obj):
        try:
            scheduling = MaintenanceScheduling.objects.get(id_maintenance_request=obj)
            return scheduling.assigned_technician.id_user if scheduling.assigned_technician else None
        except MaintenanceScheduling.DoesNotExist:
            return None