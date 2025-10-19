from rest_framework import serializers
from django.utils import timezone

from service_requests.models import ServiceRequest
from users.models.user import User


class ServiceRequestCompleteSerializer(serializers.ModelSerializer):
    """
    Serializer para finalizar una solicitud de servicio.
    Valida que la solicitud esté en estado "En proceso" (21) y no esté cancelada.
    """
    
    completion_cancellation_observations = serializers.CharField(
        required=True, 
        allow_blank=False,
        max_length=500
    )
    
    class Meta:
        model = ServiceRequest
        fields = [
            'completion_cancellation_observations',
        ]
        
    def validate(self, attrs):
        """
        Validaciones de negocio para finalización de solicitud.
        """
        instance: ServiceRequest = self.instance
        
        if not instance:
            raise serializers.ValidationError('No se encontró la solicitud a finalizar.')
        
        current_status = getattr(instance, 'request_status', None)
        current_status_id = getattr(current_status, 'id_statues', None)

        # No puede finalizar si está cancelada (23)
        if current_status_id == 23:
            raise serializers.ValidationError(
                'No se puede finalizar una solicitud que está cancelada.'
            )
        
        # Solo puede finalizar si está "En proceso" (21)
        if current_status_id != 21:
            raise serializers.ValidationError(
                'Solo se pueden finalizar solicitudes que están en proceso (estado aceptado).'
            )
        
        return attrs

    def update(self, instance: ServiceRequest, validated_data):
        """
        Actualiza la solicitud con los datos de finalización.
        Mismo patrón que ServiceRequestCancelSerializer.
        """
        # Asignar observaciones (opcional)
        instance.completion_cancellation_observations = validated_data.get(
            'completion_cancellation_observations', 
            ''
        )
        
        # Fecha: calcular automáticamente (igual que cancelar)
        instance.completion_cancellation_datetime = timezone.now()
        
        # Usuario: resolver automáticamente desde request.user.id al modelo User (PK = id_user)
        req = self.context.get('request') if self.context else None
        jwt_user = getattr(req, 'user', None) if req else None
        user_id = getattr(jwt_user, 'id', None)
        if user_id is not None:
            db_user = User.objects.filter(pk=user_id).first()
            if db_user:
                instance.completion_cancellation_user = db_user
            else:
                instance.completion_cancellation_user = None
        
        # Guardar SOLO los campos que modificamos (sin tocar request_status, modification_date, etc.)
        instance.save(update_fields=[
            'completion_cancellation_observations',
            'completion_cancellation_datetime',
            'completion_cancellation_user',
        ])
        
        return instance
