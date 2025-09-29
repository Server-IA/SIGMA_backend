from rest_framework import serializers
from maintenance.models.maintenance_request import MaintenanceRequest
from maintenance.models.maintenance_scheduling import MaintenanceScheduling

class MaintenanceRequestDetailSerializer(serializers.ModelSerializer):
    consecutivo = serializers.IntegerField(source="id_maintenance_request", read_only=True)
    machinery_serial = serializers.CharField(source="id_machinery.serial_number", read_only=True)
    machinery_name = serializers.CharField(source="id_machinery.machinery_name", read_only=True)
    requester_name = serializers.SerializerMethodField()
    maintenance_type_name = serializers.CharField(source="maintenance_type.name", read_only=True)
    fecha_solicitud = serializers.DateField(source="detected_at", read_only=True)
    priority_name = serializers.CharField(source="priority.name", read_only=True)
    status_name = serializers.CharField(source="request_status.name", read_only=True)
    responsible_user_name = serializers.SerializerMethodField()

    # Bloque de programación (si existe)
    scheduling = serializers.SerializerMethodField()

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
            "description",
            "justification",
            "responsible_user_name",
            "registration_date",
            "modification_date",
            "scheduling",
        ]

    def get_requester_name(self, obj):
        user = obj.id_responsible_user
        if not user:
            return "Generada automáticamente"
        if hasattr(user, "name") and user.name:
            return user.name
        if hasattr(user, "first_name") or hasattr(user, "last_name"):
            return f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        if hasattr(user, "username"):
            return user.username
        return "Usuario desconocido"

    def get_responsible_user_name(self, obj):
        user = obj.id_responsible_user
        if not user:
            return None
        if hasattr(user, "name") and user.name:
            return user.name
        if hasattr(user, "first_name") or hasattr(user, "last_name"):
            return f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        if hasattr(user, "username"):
            return user.username
        return "Usuario desconocido"

    def get_scheduling(self, obj):
        """
        Devuelve la programación asociada (si existe).
        """
        scheduling = obj.maintenance_schedulings.first()
        if not scheduling:
            return None

        return {
            "id_maintenance_scheduling": scheduling.id_maintenance_scheduling,
            "fecha_programada": scheduling.scheduled_at,
            "detalle": scheduling.details,
            "estado_programacion": scheduling.maintenance_scheduling_status.name if scheduling.maintenance_scheduling_status else None,
            "tecnico_asignado": self._get_user_name(scheduling.assigned_technician),
            "usuario_programador": self._get_user_name(scheduling.id_responsible_user),
            "fecha_registro": scheduling.registration_date,
            "fecha_modificacion": scheduling.modification_date,
        }

    def _get_user_name(self, user):
        if not user:
            return None
        if hasattr(user, "name") and user.name:
            return user.name
        if hasattr(user, "first_name") or hasattr(user, "last_name"):
            return f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        if hasattr(user, "username"):
            return user.username
        return "Usuario desconocido"