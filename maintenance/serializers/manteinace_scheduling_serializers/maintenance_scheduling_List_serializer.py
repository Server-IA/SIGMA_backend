from rest_framework import serializers
from maintenance.models.maintenance_scheduling import MaintenanceScheduling
from datetime import date


class MaintenanceSchedulingListSerializer(serializers.ModelSerializer):
    machinery_serial = serializers.CharField(source="id_machinery.serial_number", read_only=True)
    machinery_name = serializers.CharField(source="id_machinery.machinery_name", read_only=True)
    machinery_image = serializers.CharField(source="id_machinery.image_path", read_only=True)
    technician_name = serializers.SerializerMethodField()
    status_name = serializers.CharField(source="maintenance_scheduling_status.name", read_only=True)
    fecha_mantenimiento = serializers.DateTimeField(source="scheduled_at", read_only=True)
    fecha_color = serializers.SerializerMethodField()
    can_register_report = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceScheduling
        fields = [
            "id_maintenance_scheduling",
            "machinery_image",
            "machinery_serial",
            "machinery_name",
            "fecha_mantenimiento",
            "fecha_color",
            "technician_name",
            "status_name",
            "can_register_report",
        ]

    def get_technician_name(self, obj):
        user = obj.assigned_technician
        if not user:
            return None
        if hasattr(user, "name") and user.name:
            return user.name
        if hasattr(user, "first_name") or hasattr(user, "last_name"):
            return f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
        if hasattr(user, "username"):
            return user.username
        return "Usuario desconocido"

    def get_fecha_color(self, obj):
        hoy = date.today()
        fecha = obj.scheduled_at.date()
        if fecha < hoy:
            return "rojo"  # vencido
        elif fecha == hoy:
            return "amarillo"  # hoy
        return "verde"  # vigente

    def get_can_register_report(self, obj):
        """
        Solo disponible si el estado = 'Realizado'.
        Ajusta el ID o nombre de estado según tu parametrización real.
        """
        return obj.maintenance_scheduling_status.name.lower() == "realizado"
