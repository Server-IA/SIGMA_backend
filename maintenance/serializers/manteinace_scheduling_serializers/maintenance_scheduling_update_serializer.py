import requests
import os
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
        )
        read_only_fields = ('registration_date',)

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
        Valida:
        1. Disponibilidad del técnico para el `scheduled_at`
        2. Que el mantenimiento no esté en estado completado (id=15)
        3. Establece el usuario responsable desde el contexto de la petición
        """
        instance: MaintenanceScheduling = self.instance
        
        # Verificar si el mantenimiento ya está completado (estado_id=15) o cancelado (estado_id=14)
        if hasattr(instance, 'maintenance_scheduling_status'):
            status_id = instance.maintenance_scheduling_status_id
            if status_id == 15:
                raise serializers.ValidationError(
                    "No se puede actualizar un mantenimiento que ya ha sido completado."
                )
            if status_id == 14:
                raise serializers.ValidationError(
                    "No se puede actualizar un mantenimiento que ha sido cancelado."
                )
            
        # Establecer el usuario responsable desde el contexto de la petición
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            attrs['id_responsible_user_id'] = request.user.id
            
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


    def _send_technician_notification_email(self, instance, previous_technician=None):
        """
        Envía una notificación por email al técnico asignado después de actualizar el agendamiento.
        Si hay un previous_technician, se notifica al nuevo técnico.
        Si no hay previous_technician, se notifica al técnico actual de los cambios.
        """
        try:
            auth_service_url = os.getenv('AUTH_SERVICE_URL')
            if not auth_service_url:
                return
                
            notification_endpoint = f"{auth_service_url.rstrip('/')}/users/users/send-technician-notification"
            
            # Determinar a quién notificar
            technician_to_notify = instance.assigned_technician
            
            notification_data = {
                "scheduled_at": instance.scheduled_at.isoformat(),
                "details": instance.details,
                "assigned_technician": technician_to_notify.pk
            }
            
            response = requests.post(
                notification_endpoint,
                json=notification_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
                
        except Exception:
            # Silenciar errores - no debe afectar la actualización principal
            pass

    @transaction.atomic
    def update(self, instance: MaintenanceScheduling, validated_data):
        # Guardar el técnico anterior si está siendo actualizado
        previous_technician = None
        if "assigned_technician" in validated_data and instance.assigned_technician != validated_data["assigned_technician"]:
            previous_technician = instance.assigned_technician
        
        # Update only allowed fields
        for field in ("scheduled_at", "details", "assigned_technician", "maintenance_type", "id_responsible_user_id"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        # Save with update_fields to only update specific fields
        instance.save(
            update_fields=[
                "scheduled_at",
                "details",
                "assigned_technician",
                "maintenance_type",
                "id_responsible_user_id",
                "modification_date",  # auto_now
            ]
        )
        
        # Enviar notificación al nuevo técnico si hubo cambio
        if previous_technician:
            self._send_technician_notification_email(instance, previous_technician)
        # Si no hubo cambio de técnico pero sí actualización de otros datos, notificar al técnico actual
        elif any(field in validated_data for field in ["scheduled_at", "details"]):
            self._send_technician_notification_email(instance)
            
        return instance


