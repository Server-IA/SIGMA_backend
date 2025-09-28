from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from maintenance.models import MaintenanceScheduling
from parameterization.models import TypesCategory


class MaintenanceSchedulingUpdateSerializer(serializers.ModelSerializer):
    """
    Actualiza un mantenimiento programado.
    Campos permitidos:
      - scheduled_at (fecha y hora)
      - details (≤ 350)
      - assigned_technician
      - maintenance_type (categoría id=12)
      - id_responsible_user (auditoría)
    """

    class Meta:
        model = MaintenanceScheduling
        fields = (
            "scheduled_at",
            "details",
            "assigned_technician",
            "maintenance_type",
            "id_responsible_user",
        )

    def validate_scheduled_at(self, value):
        # No permitir fechas pasadas
        if value < timezone.now():
            raise serializers.ValidationError(
                "La fecha y hora programada no puede estar en el pasado."
            )
        return value

    def validate_details(self, value: str):
        if value is None:
            return value
        if len(value) > 350:
            raise serializers.ValidationError(
                "Los detalles no pueden exceder 350 caracteres."
            )
        return value.strip()

    def validate_maintenance_type(self, value):
        """
        Validar que el tipo de mantenimiento pertenezca a la categoría con id=12.
        """
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

    def validate(self, attrs):
        """
        Verifica disponibilidad del técnico para el `scheduled_at`.
        """
        instance: MaintenanceScheduling = self.instance
        scheduled_at = attrs.get("scheduled_at", instance.scheduled_at)
        technician = attrs.get("assigned_technician", instance.assigned_technician)

        clash = (
            MaintenanceScheduling.objects.filter(
                assigned_technician=technician, scheduled_at=scheduled_at
            )
            .exclude(pk=instance.pk)
            .exists()
        )
        if clash:
            raise serializers.ValidationError(
                "El técnico seleccionado no está disponible en la fecha y hora indicadas."
            )
        return attrs

    @transaction.atomic
    def update(self, instance: MaintenanceScheduling, validated_data):
        # Asignar solo campos permitidos
        for field in ("scheduled_at", "details", "assigned_technician", "maintenance_type", "id_responsible_user"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save(
            update_fields=[
                "scheduled_at",
                "details",
                "assigned_technician",
                "maintenance_type",
                "id_responsible_user",
                "modification_date",  # auto_now
            ]
        )
        return instance


