from django.utils import timezone
from django.db import transaction
from rest_framework import serializers

from maintenance.models import (
    MaintenanceRequest,
    MaintenanceScheduling,
    MaintenanceSchedulingConsecutive,
)
from parameterization.models import TypesCategory, Statues


class MaintenanceSchedulingFromRequestCreateSerializer(serializers.ModelSerializer):
    id_maintenance_request = serializers.PrimaryKeyRelatedField(
        queryset=MaintenanceRequest.objects.all(), required=True
    )

    class Meta:
        model = MaintenanceScheduling
        fields = (
            "id_maintenance_request",
            "id_machinery",
            "scheduled_at",
            "details",
            "assigned_technician",
            "maintenance_type",
            "id_consecutive",
            "id_responsible_user",
        )
        read_only_fields = ("id_consecutive", "id_machinery")

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

        # 3) Evitar programar dos veces la misma solicitud
        if req:
            already_scheduled = MaintenanceScheduling.objects.filter(id_maintenance_request=req).exists()
            if already_scheduled:
                raise serializers.ValidationError(
                    {"id_maintenance_request": "La solicitud ya cuenta con un mantenimiento programado."}
                )
            # 4) Si la solicitud ya está en estado Aceptado (id=11), no permitir reprogramar desde esta vía
            try:
                current_status_id = getattr(getattr(req, "request_status", None), "id_statues", None)
            except Exception:
                current_status_id = None
            if current_status_id == 11:
                raise serializers.ValidationError(
                    {"request_status": "La solicitud ya se encuentra en estado 'Aceptado'. No se puede programar nuevamente."}
                )
        return attrs

    def _generate_consecutive(self):
        year = timezone.now().year
        with transaction.atomic():
            last = (
                MaintenanceSchedulingConsecutive.objects
                .filter(anio=year)
                .order_by("-code")
                .first()
            )
            next_code = (last.code + 1) if last else 1
            return MaintenanceSchedulingConsecutive.objects.create(anio=year, code=next_code)

    def create(self, validated_data):
        request_obj: MaintenanceRequest = validated_data.pop("id_maintenance_request")

        # Pre-cargar id_machinery desde la solicitud si no fue proporcionado explícitamente
        validated_data["id_machinery"] = request_obj.id_machinery

        # Si no envían maintenance_type, usar el de la solicitud
        if not validated_data.get("maintenance_type"):
            validated_data["maintenance_type"] = request_obj.maintenance_type

        # Fechas de auditoría
        now = timezone.now()
        validated_data["registration_date"] = now
        validated_data["modification_date"] = now

        with transaction.atomic():
            consecutive = self._generate_consecutive()
            validated_data["id_consecutive"] = consecutive
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
            request_obj.save(update_fields=["request_status", "modification_date"])
        return instance
