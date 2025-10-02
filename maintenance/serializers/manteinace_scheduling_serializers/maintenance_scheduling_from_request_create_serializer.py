import requests
import os
import json
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Max
from rest_framework import serializers

from maintenance.models import (
    MaintenanceRequest,
    MaintenanceScheduling,
)
from parameterization.models import TypesCategory, Statues


class MaintenanceSchedulingFromRequestCreateSerializer(serializers.ModelSerializer):
    id_maintenance_request = serializers.PrimaryKeyRelatedField(
        queryset=MaintenanceRequest.objects.all(), required=True
    )
    
    def generate_scheduling_id(self):
        current_year = timezone.now().year
        # Find the highest request number for the current year
        max_scheduling = MaintenanceScheduling.objects.filter(
            id_maintenance_scheduling__startswith=f'PRO-{current_year}'
        ).aggregate(Max('id_maintenance_scheduling'))
        
        if max_scheduling['id_maintenance_scheduling__max']:
            # Extract the number part and increment it
            last_number = int(max_scheduling['id_maintenance_scheduling__max'].split('-')[-1])
            new_number = last_number + 1
        else:
            # First scheduling of the year
            new_number = 1
            
        return f'PRO-{current_year}-{new_number:04d}'

    class Meta:
        model = MaintenanceScheduling
        fields = (
            "id_maintenance_request",
            "id_machinery",
            "scheduled_at",
            "details",
            "assigned_technician",
            "maintenance_type",
            "id_responsible_user",
        )
        read_only_fields = ("id_machinery", "id_responsible_user")

    def validate(self, attrs):
        # Obtenemos el usuario del contexto (que vendrá de la vista)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            # Usamos solo el ID del usuario
            attrs['id_responsible_user_id'] = request.user.id

        # Validamos que la fecha no sea pasada
        scheduled_at = attrs.get('scheduled_at')
        if scheduled_at and scheduled_at < timezone.now():
            raise serializers.ValidationError({"scheduled_at": "La fecha y hora programada no puede estar en el pasado."})
            
        return attrs

    def validate_scheduled_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("La fecha y hora programada no puede estar en el pasado.")
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

    def validate(self, attrs):
        scheduled_at = attrs.get("scheduled_at")
        technician = attrs.get("assigned_technician")
        req: MaintenanceRequest = attrs.get("id_maintenance_request")

        # 1) Disponibilidad del técnico (conflicto por misma fecha/hora)
        if scheduled_at and technician:
            clash = MaintenanceScheduling.objects.filter(
                assigned_technician=technician,
                scheduled_at=scheduled_at,
            ).exists()
            if clash:
                raise serializers.ValidationError(
                    {"assigned_technician": "El técnico seleccionado no está disponible en la fecha y hora indicadas."}
                )

        # 2) La maquinaria debe estar activa (estado operativo id=4)
        if req:
            status_id = getattr(getattr(req.id_machinery, "machinery_operational_status", None), "id_statues", None)
            if status_id != 4:
                raise serializers.ValidationError(
                    {"id_machinery": "La maquinaria asociada no está en estado 'Activo'."}
                )

        # 3) Validar el estado actual de la solicitud primero
        if req:
            try:
                current_status_id = getattr(getattr(req, "request_status", None), "id_statues", None)
            except Exception:
                current_status_id = None
                
            if current_status_id == 11:  # Aceptado
                raise serializers.ValidationError(
                    {"request_status": "La solicitud ya se encuentra en estado 'Aceptado'. No se puede programar nuevamente."}
                )
                
            if current_status_id == 12:  # Rechazado
                raise serializers.ValidationError(
                    {"request_status": "No se puede programar una solicitud que ha sido rechazada."}
                )
            
            # 4) Validar si ya existe un mantenimiento programado para esta solicitud
            already_scheduled = MaintenanceScheduling.objects.filter(id_maintenance_request=req).exists()
            if already_scheduled:
                raise serializers.ValidationError(
                    {"id_maintenance_request": "La solicitud ya cuenta con un mantenimiento programado."}
                )
        return attrs


    def create(self, validated_data):
        request_obj: MaintenanceRequest = validated_data.pop("id_maintenance_request")
        
        # Obtener el usuario del contexto
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user or not hasattr(request.user, 'id'):
            raise serializers.ValidationError("No se pudo determinar el usuario responsable.")
            
        # Obtener la instancia real de User desde la base de datos
        from users.models import User
        try:
            current_user = User.objects.get(pk=request.user.id)
        except User.DoesNotExist:
            raise serializers.ValidationError("El usuario autenticado no existe en la base de datos.")
            
        now = timezone.now()

        # Update only response_date and id_response_user without triggering modification_date update
        MaintenanceRequest.objects.filter(pk=request_obj.pk).update(
            id_response_user=current_user,
            response_date=now,
            # Explicitly prevent modification_date from updating
            modification_date=models.F('modification_date')
        )

        # Pre-cargar id_machinery desde la solicitud si no fue proporcionado explícitamente
        validated_data["id_machinery"] = request_obj.id_machinery

        # Si no envían maintenance_type, usar el de la solicitud
        if not validated_data.get("maintenance_type"):
            validated_data["maintenance_type"] = request_obj.maintenance_type

        # Establecer el usuario responsable como el usuario actual (instancia de User)
        validated_data['id_responsible_user'] = current_user
        
        # Fechas de auditoría
        validated_data["registration_date"] = now
        validated_data["modification_date"] = now

        with transaction.atomic():
            # Obtener el estado 13 (Programado) para el mantenimiento
            try:
                status = Statues.objects.get(id_statues=13)
            except Statues.DoesNotExist:
                raise serializers.ValidationError("No se encontró el estado 'Programado' (id=13) en la parametrización.")
                
            # Asignar el estado 13 al mantenimiento programado
            validated_data["maintenance_scheduling_status"] = status
            
            # Generate the custom ID
            validated_data['id_maintenance_scheduling'] = self.generate_scheduling_id()
            
            # Crear la instancia del mantenimiento programado
            instance = MaintenanceScheduling.objects.create(
                id_maintenance_request=request_obj,
                **validated_data,
            )
            
            # Cambiar el estado de la solicitud a "Aceptado" (id=11)
            try:
                accepted = Statues.objects.get(id_statues=11)
            except Statues.DoesNotExist:
                raise serializers.ValidationError("No se encontró el estado 'Aceptado' (id=11) en la parametrización.")
           
            request_obj.request_status = accepted
            request_obj.modification_date = timezone.now()
            request_obj.save(update_fields=["request_status"])
        
        # Enviar notificación por email al técnico asignado
        self._send_technician_notification_email(instance)
        
        return instance

    def _send_technician_notification_email(self, instance):
        """
        Envía una notificación por email al técnico asignado después de crear el agendamiento
        """
        try:
            auth_service_url = os.getenv('AUTH_SERVICE_URL')
            if not auth_service_url:
                return
                
            notification_endpoint = f"{auth_service_url.rstrip('/')}/users/users/send-technician-notification"
            
            notification_data = {
                "scheduled_at": instance.scheduled_at.isoformat(),
                "details": instance.details,
                "assigned_technician": instance.assigned_technician.pk
            }
            
            response = requests.post(
                notification_endpoint,
                json=notification_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
                
        except Exception:
            # Silenciar errores - no debe afectar el agendamiento principal
            pass
