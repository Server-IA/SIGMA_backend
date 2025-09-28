from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from maintenance.models import MaintenanceScheduling, MaintenanceSchedulingConsecutive
from parameterization.models import TypesCategory


class MaintenanceSchedulingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceScheduling
        fields = (
            "id_machinery",
            "scheduled_at",
            "details",
            "assigned_technician",
            "maintenance_type",
            "id_consecutive",
            "id_responsible_user",
        )
        read_only_fields = ("id_consecutive", "id_responsible_user")

    def validate_scheduled_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("La fecha y hora programada no puede estar en el pasado.")
        return value

    def validate(self, attrs):
        # Obtenemos el usuario del contexto (que vendrá de la vista)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and hasattr(request.user, 'id'):
            # Usamos solo el ID del usuario
            attrs['id_responsible_user_id'] = request.user.id

        scheduled_at = attrs.get("scheduled_at")
        technician = attrs.get("assigned_technician")

        # No sugerimos valores desde backend; el front debe enviarlos.
        # Solo validamos conflictos si ambos vienen presentes (DRF/modelo ya marcan como requeridos).
        if scheduled_at and technician:
            clash = MaintenanceScheduling.objects.filter(
                assigned_technician=technician,
                scheduled_at=scheduled_at,
            )
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError("El técnico seleccionado no está disponible en la fecha y hora indicadas.")

        return attrs

    def validate_maintenance_type(self, value):
        """
        Validar que el tipo de mantenimiento pertenezca a la categoría con id = 12.
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

    def _generate_consecutive(self) -> MaintenanceSchedulingConsecutive:
        # Generar consecutivo por año: tomar el año actual y el siguiente código entero disponible.
        # Si no hay registros para el año, usar code = 1.
        now = timezone.now()
        year = now.year
        with transaction.atomic():
            last = (
                MaintenanceSchedulingConsecutive.objects
                .filter(anio=year)
                .order_by("-code")
                .first()
            )
            next_code = (last.code + 1) if last else 1
            obj = MaintenanceSchedulingConsecutive.objects.create(anio=year, code=next_code)
        return obj

    def create(self, validated_data):
        request = self.context.get("request")

        with transaction.atomic():
            # Setear fechas de auditoría explícitamente a la fecha actual
            now = timezone.now()
            validated_data["registration_date"] = now
            validated_data["modification_date"] = now

            consecutive = self._generate_consecutive()
            validated_data["id_consecutive"] = consecutive
            instance = MaintenanceScheduling.objects.create(**validated_data)

        # Notificaciones (correo/sistema) deberían dispararse en capa de aplicación (View/Signal)
        return instance

