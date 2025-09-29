from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from maintenance.models import MaintenanceRequest
from parameterization.models import Statues


class MaintenanceRequestRejectSerializer(serializers.Serializer):
    justification = serializers.CharField(
        max_length=300, 
        allow_blank=False, 
        required=True, 
        trim_whitespace=True,
        error_messages={
            'blank': 'La justificación es obligatoria',
            'required': 'La justificación es obligatoria'
        }
    )

    def validate(self, attrs):
        instance: MaintenanceRequest = self.context["instance"]
        status_id = getattr(instance.request_status, "id_statues", None)

        if status_id == 11:  # Aceptado
            raise serializers.ValidationError("No se puede rechazar una solicitud que ya fue aceptada.")
            
        if status_id == 12:  # Rechazado
            raise serializers.ValidationError("La solicitud ya fue rechazada previamente.")
            
        return attrs

    def save(self, **kwargs):
        instance: MaintenanceRequest = self.context["instance"]
        justification = self.validated_data["justification"]

        with transaction.atomic():
            try:
                rejected_status = Statues.objects.get(id_statues=12)  # ID para estado Rechazado
            except Statues.DoesNotExist:
                raise serializers.ValidationError(
                    "No se encontró el estado 'Rechazado' (id=12) en la parametrización."
                )

            instance.justification = justification
            instance.request_status = rejected_status
            instance.modification_date = timezone.now()
            instance.save(update_fields=["justification", "request_status", "modification_date"])

        return instance
