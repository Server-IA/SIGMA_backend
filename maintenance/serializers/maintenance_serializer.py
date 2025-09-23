# maintenance/serializers/maintenance_serializer.py
from rest_framework import serializers
from maintenance.models import Maintenance

class MaintenanceSerializer(serializers.ModelSerializer):
    # Solo para mostrar el id del responsable si se requiere en retrieve
    id_responsible_user = serializers.IntegerField(
        source="id_responsible_user_id", read_only=True
    )

    name = serializers.CharField(
        max_length=100,
        error_messages={
            "blank": "El nombre es obligatorio.",
            "max_length": "El nombre no puede exceder 100 caracteres.",
        },
    )
    description = serializers.CharField(
        max_length=300,
        trim_whitespace=True,
        error_messages={
            "max_length": "La descripción no puede exceder 300 caracteres.",
            "blank": "La descripción es obligatoria.",
            "required": "La descripción es obligatoria.",
        },
    )

    class Meta:
        model = Maintenance
        # Para create/update/retrieve trabajamos con los IDs de tipo/estado
        fields = [
            "id_maintenance",
            "name",
            "description",
            "maintenance_type",    # FK -> Types (categoria mantenimiento)
            "maintenance_status",  # FK -> Types (si lo usas) o lo puedes omitir si no aplica
            "id_responsible_user",
            "registration_date",
            "modification_date",
        ]
        read_only_fields = ("id_maintenance", "id_responsible_user", "registration_date", "modification_date")

    def validate_name(self, value):
        value = value.strip()
        if Maintenance.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un mantenimiento con este nombre.")
        return value


class MaintenanceListSerializer(serializers.ModelSerializer):
    # nombres legibles para el listado
    maintenance_type_name = serializers.CharField(
        source="maintenance_type.name", read_only=True
    )
    # estado tomado del status del TYPE (Types.id_statues -> Statues.name)
    status_name = serializers.CharField(
        source="maintenance_type.id_statues.name", read_only=True
    )

    class Meta:
        model = Maintenance
        fields = [
            "id_maintenance",
            "name",
            "description",
            "maintenance_type_name",
            "status_name",
        ]