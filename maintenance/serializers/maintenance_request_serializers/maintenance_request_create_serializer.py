from django.utils import timezone
from rest_framework import serializers

from maintenance.models import MaintenanceRequest
from parameterization.models import TypesCategory, Statues


class MaintenanceRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequest
        fields = (
            "id_machinery",
            "maintenance_type",
            "description",
            "priority",
            "detected_at",
            "id_responsible_user",
        )

    def validate_detected_at(self, value):
        # La fecha de detección no puede ser futura
        if value > timezone.now().date():
            raise serializers.ValidationError("La fecha de detección no puede ser futura.")
        return value

    def validate_id_machinery(self, value):
        # La maquinaria debe estar activa (id de estado operativo = 4)
        try:
            status_id = getattr(value.machinery_operational_status, "id_statues", None)
        except Exception:
            status_id = None
        if status_id != 4:
            raise serializers.ValidationError("La maquinaria no está en estado activo.")
        return value

    def validate_maintenance_type(self, value):
        # Debe pertenecer a la categoría con id = 12
        if getattr(value, "id_types_categories_id", None) != 12:
            try:
                expected_category = TypesCategory.objects.get(id_types_categories=12)
                raise serializers.ValidationError(
                    f"El tipo de mantenimiento debe pertenecer a la categoría '{expected_category.name}'."
                )
            except TypesCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "La categoría de tipos requerida (id=12) no existe en la parametrización."
                )
        return value

    def create(self, validated_data):
        # Estado inicial por defecto: "Pendiente"
        try:
            pending_status = Statues.objects.get(id_statues=10)
        except Statues.DoesNotExist:
            raise serializers.ValidationError("No se encontró el estado 'Pendiente' (id=10) en la parametrización.")

        validated_data["request_status"] = pending_status
        # Guardar fechas explícitas si deseas forzar (aunque el modelo ya usa auto_now)
        validated_data["registration_date"] = timezone.now()
        validated_data["modification_date"] = timezone.now()

        # Crear la solicitud sin consecutivo (solo registro de solicitud, no programación)
        instance = MaintenanceRequest.objects.create(**validated_data)
        return instance
