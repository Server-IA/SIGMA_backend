from rest_framework import serializers
from django.utils import timezone
from datetime import datetime

from service_requests.models import ServiceRequest
from users.models.user import User


class ServiceRequestCompleteSerializer(serializers.ModelSerializer):
    """
    Serializer para finalizar una solicitud de servicio.
    Valida que la solicitud esté en estado "En proceso" (22) y no esté cancelada.
    """
    
    # Campos adicionales para fecha y hora de finalización
    completion_date = serializers.DateField(
        required=True,
        error_messages={
            'required': 'La fecha de finalización es obligatoria.',
            'invalid': 'Formato de fecha inválido. Use YYYY-MM-DD.'
        }
    )
    completion_time = serializers.TimeField(
        required=True,
        error_messages={
            'required': 'La hora de finalización es obligatoria.',
            'invalid': 'Formato de hora inválido. Use HH:MM:SS.'
        }
    )
    
    class Meta:
        model = ServiceRequest
        fields = [
            'completion_cancellation_observations',
            'completion_date',
            'completion_time',
        ]
        extra_kwargs = {
            'completion_cancellation_observations': {
                'required': False,
                'allow_blank': True,
                'max_length': 500
            }
        }
        
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
        
        # Solo puede finalizar si está "En proceso" (22)
        if current_status_id != 22:
            raise serializers.ValidationError(
                'Solo se pueden finalizar solicitudes que están en proceso (estado aceptado).'
            )
        
        # Validar que la fecha no sea futura
        completion_date = attrs.get('completion_date')
        if completion_date and completion_date > timezone.now().date():
            raise serializers.ValidationError(
                'La fecha de finalización no puede ser futura.'
            )
        
        # Validar que la fecha no sea anterior a la fecha de inicio programada
        if completion_date and instance.scheduled_start_date:
            if completion_date < instance.scheduled_start_date:
                raise serializers.ValidationError(
                    'La fecha de finalización no puede ser anterior a la fecha de inicio programada.'
                )
        
        return attrs

    def update(self, instance: ServiceRequest, validated_data):
        """
        Actualiza la solicitud con los datos de finalización.
        """
        # Remover campos personalizados que no están en el modelo
        completion_date = validated_data.pop('completion_date')
        completion_time = validated_data.pop('completion_time')
        
        # Combinar fecha y hora en un datetime
        completion_datetime = datetime.combine(completion_date, completion_time)
        
        # Convertir a timezone aware
        completion_datetime = timezone.make_aware(
            completion_datetime, 
            timezone.get_current_timezone()
        )
        
        # Asignar observaciones (opcional)
        instance.completion_cancellation_observations = validated_data.get(
            'completion_cancellation_observations', 
            ''
        )
        
        # Asignar fecha/hora de finalización
        instance.completion_cancellation_datetime = completion_datetime
        
        # Resolver usuario desde JWT (mismo patrón que cancelación)
        req = self.context.get('request') if self.context else None
        jwt_user = getattr(req, 'user', None) if req else None
        user_id = getattr(jwt_user, 'id', None)
        
        if user_id is not None:
            db_user = User.objects.filter(pk=user_id).first()
            if db_user:
                instance.completion_cancellation_user = db_user
            else:
                instance.completion_cancellation_user = None
        
        # Guardar cambios (sin actualizar request_status aquí, se hace en el viewset)
        instance.save(update_fields=[
            'completion_cancellation_observations',
            'completion_cancellation_datetime',
            'completion_cancellation_user',
        ])
        
        return instance
