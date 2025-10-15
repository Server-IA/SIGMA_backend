from rest_framework import serializers
from django.utils import timezone

from service_requests.models import ServiceRequest
from users.models.user import User


class ServiceRequestCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = [
            'completion_cancellation_observations',
        ]
        
    def validate(self, attrs):
        # Validaciones de estado en el serializer
        instance: ServiceRequest = self.instance
        if not instance:
            raise serializers.ValidationError('No se encontró la solicitud a cancelar.')
        current_status = getattr(instance, 'request_status', None)
        current_status_id = getattr(current_status, 'id_statues', None)

        if current_status_id in (22, 23):
            raise serializers.ValidationError('La solicitud no puede cancelarse porque ya está aceptada o cancelada.')
        if current_status_id != 20:
            raise serializers.ValidationError('Solo se pueden cancelar solicitudes en estado pendiente.')

        # Observaciones opcionalmente podrías validar vacío si negocio lo exige
        return attrs

    def update(self, instance: ServiceRequest, validated_data):
        # Set cancellation metadata
        instance.completion_cancellation_observations = validated_data.get('completion_cancellation_observations', '')

        # Fecha: calcular automáticamente
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

        instance.save(update_fields=[
            'completion_cancellation_observations',
            'completion_cancellation_datetime',
            'completion_cancellation_user',
        ])
        return instance
