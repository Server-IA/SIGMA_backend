from rest_framework import serializers
from maintenance.models.maintenance_scheduling import MaintenanceScheduling


class MaintenanceSchedulingListSerializer(serializers.ModelSerializer):
    machinery_serial = serializers.CharField(source="id_machinery.serial_number", read_only=True)
    machinery_name = serializers.CharField(source="id_machinery.machinery_name", read_only=True)
    secondary_type_name = serializers.CharField(source="id_machinery.machinery_secondary_type.name", read_only=True)
    machinery_image = serializers.CharField(source="id_machinery.image_path", read_only=True)
    assigned_technician_id = serializers.SerializerMethodField()
    maintenance_type_name = serializers.CharField(source="maintenance_type.name", read_only=True)
    status_name = serializers.CharField(source="maintenance_scheduling_status.name", read_only=True)
    status_id = serializers.IntegerField(source="maintenance_scheduling_status.id_statues", read_only=True)
    scheduled_at = serializers.DateTimeField(read_only=True)
    request_creation_date = serializers.DateTimeField(source="id_maintenance_request.registration_date", read_only=True, allow_null=True)

    class Meta:
        model = MaintenanceScheduling
        fields = [
            "id_maintenance_scheduling",
            "machinery_serial",
            "machinery_name",
            "secondary_type_name",
            "machinery_image",
            "scheduled_at",
            "assigned_technician_id",
            "maintenance_type",
            "maintenance_type_name",
            "status_id",
            "status_name",
            "request_creation_date"
        ]

    def get_assigned_technician_id(self, obj):
        return obj.assigned_technician.id_user if obj.assigned_technician else None
