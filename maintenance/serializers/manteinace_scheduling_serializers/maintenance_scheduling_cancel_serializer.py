from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from maintenance.models import MaintenanceScheduling
from parameterization.models import Statues


class MaintenanceSchedulingCancelSerializer(serializers.Serializer):
    justification = serializers.CharField(
        max_length=300, allow_blank=False, required=True, trim_whitespace=True
    )

    def validate(self, attrs):
        instance: MaintenanceScheduling = self.context["instance"]
        status_id = getattr(getattr(instance, "maintenance_scheduling_status", None), "id_statues", None)

        if status_id == 14:
            raise serializers.ValidationError("El mantenimiento programado ya fue cancelado.")
        if status_id == 15:
            raise serializers.ValidationError("El mantenimiento ya fue realizado y no puede cancelarse.")
        return attrs

    def save(self, **kwargs):
        instance: MaintenanceScheduling = self.context["instance"]
        justification = self.validated_data["justification"]

        with transaction.atomic():
            try:
                canceled_status = Statues.objects.get(id_statues=14)
            except Statues.DoesNotExist:
                raise serializers.ValidationError("No se encontró el estado 'Cancelado' (id=14) en la parametrización.")

            instance.justification = justification
            instance.maintenance_scheduling_status = canceled_status
            instance.modification_date = timezone.now()
            instance.save(update_fields=["justification", "maintenance_scheduling_status", "modification_date"])

        return instance


