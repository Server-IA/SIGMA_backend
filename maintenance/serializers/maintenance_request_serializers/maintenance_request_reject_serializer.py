from django.db import transaction, models
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
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user or not hasattr(request.user, 'id'):
            raise serializers.ValidationError("No se pudo determinar el usuario que responde.")
            
        instance: MaintenanceRequest = self.context["instance"]
        justification = self.validated_data["justification"]
        now = timezone.now()

        with transaction.atomic():
            try:
                rejected_status = Statues.objects.get(id_statues=12)  # ID para estado Rechazado
            except Statues.DoesNotExist:
                raise serializers.ValidationError(
                    "No se encontró el estado 'Rechazado' (id=12) en la parametrización."
                )
            
            # Update the instance with direct database update to avoid auto_now on modification_date
            MaintenanceRequest.objects.filter(pk=instance.pk).update(
                justification=justification,
                request_status=rejected_status,
                id_response_user_id=request.user.id,  # Use user.id instead of user object
                response_date=now,
                modification_date=models.F('modification_date')  # Keep original modification_date
            )

        return instance
