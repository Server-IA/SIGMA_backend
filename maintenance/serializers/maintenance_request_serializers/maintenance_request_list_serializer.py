from rest_framework import serializers
from maintenance.models.maintenance_request import MaintenanceRequest


class MaintenanceRequestListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar solicitudes de mantenimiento (manuales y automáticas).
    Cumple con los criterios de aceptación de la HU.
    """

    id = serializers.IntegerField(source="id_maintenance_request", read_only=True)
    machinery_serial = serializers.CharField(source="id_machinery.serial_number", read_only=True)
    machinery_name = serializers.CharField(source="id_machinery.machinery_name", read_only=True)
    requester_id = serializers.SerializerMethodField()
    maintenance_type_name = serializers.CharField(source="maintenance_type.name", read_only=True)
    fecha_solicitud = serializers.DateField(source="detected_at", read_only=True)
    priority_name = serializers.CharField(source="priority.name", read_only=True)
    status_name = serializers.CharField(source="request_status.name", read_only=True)
    status_id = serializers.IntegerField(source="request_status.id_statues", read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "machinery_serial",
            "machinery_name",
            "requester_id",
            "maintenance_type_name",
            "fecha_solicitud",
            "priority_name",
            "status_name",
            "status_id",
        ]

    def get_requester_id(self, obj):
        """
        Devuelve el ID del usuario responsable o 'Automatico' si fue generada automáticamente.
        """
        user = obj.id_responsible_user
        return user.id_user if user else "Automatico"
