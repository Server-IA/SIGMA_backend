from rest_framework import serializers
from maintenance.models.maintenance_request import MaintenanceRequest


class MaintenanceRequestListSerializer(serializers.ModelSerializer):
    """
    Serializer para listar solicitudes de mantenimiento (manuales y automáticas).
    Cumple con los criterios de aceptación de la HU.
    """

    consecutivo = serializers.IntegerField(source="id_maintenance_request", read_only=True)
    machinery_serial = serializers.CharField(source="id_machinery.serial_number", read_only=True)
    machinery_name = serializers.CharField(source="id_machinery.machinery_name", read_only=True)
    requester_name = serializers.SerializerMethodField()
    maintenance_type_name = serializers.CharField(source="maintenance_type.name", read_only=True)
    fecha_solicitud = serializers.DateField(source="detected_at", read_only=True)
    priority_name = serializers.CharField(source="priority.name", read_only=True)
    status_name = serializers.CharField(source="request_status.name", read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = [
            "consecutivo",
            "machinery_serial",
            "machinery_name",
            "requester_name",
            "maintenance_type_name",
            "fecha_solicitud",
            "priority_name",
            "status_name",
        ]

    def get_requester_name(self, obj):
        """
        Devuelve el nombre del solicitante o 'Generada automáticamente'.
        Se adapta a distintos modelos de usuario.
        """
        user = obj.id_responsible_user
        if not user:
            return "Generada automáticamente"

        # Caso 1: el modelo tiene "name"
        if hasattr(user, "name") and user.name:
            return user.name

        # Caso 2: el modelo tiene "first_name" y "last_name"
        if hasattr(user, "first_name") or hasattr(user, "last_name"):
            return f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()

        # Caso 3: fallback al username
        if hasattr(user, "username"):
            return user.username

        return "Usuario desconocido"
