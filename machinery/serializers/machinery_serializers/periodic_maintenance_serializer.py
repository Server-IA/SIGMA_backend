# machinery/serializers/machinery_serializers/periodic_maintenance_serializer.py
from rest_framework import serializers
from machinery.models import PeriodicMaintenanceScheduling, Machinery
from maintenance.models.maintenance import Maintenance


class PeriodicMaintenanceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de mantenimientos periódicos.
    Campos obligatorios:
        - id_machinery
        - id_maintenance
        - Una de las dos medidas: usage_hours o distance_km
    """
    id_machinery = serializers.IntegerField(write_only=True, required=False)
    id_maintenance = serializers.IntegerField(write_only=True, required=False)

    usage_hours = serializers.IntegerField(
        min_value=1, required=False,
        error_messages={
            "min_value": "Las horas de uso deben ser mayores a 0.",
            "invalid": "Las horas de uso deben ser un número entero.",
            "null": "Las horas de uso no pueden ser nulas.",
        },
    )
    distance_km = serializers.IntegerField(
        min_value=1, required=False,
        error_messages={
            "min_value": "La distancia debe ser mayor a 0.",
            "invalid": "La distancia debe ser un número entero.",
            "null": "La distancia no puede ser nula.",
        },
    )

    class Meta:
        model = PeriodicMaintenanceScheduling
        fields = (
            "id_periodic_maintenance_scheduling",
            "id_machinery",
            "id_maintenance",
            "usage_hours",
            "distance_km",
        )
        read_only_fields = ("id_periodic_maintenance_scheduling",)

    def _resolve_ids(self, attrs):
        mach_id = attrs.get("id_machinery", getattr(self.instance, "machinery_id", None))
        maint_id = attrs.get("id_maintenance", getattr(self.instance, "maintenance_id", None))
        return mach_id, maint_id

    def validate(self, attrs):
        is_create = self.instance is None
        id_machinery, id_maintenance = self._resolve_ids(attrs)

        if is_create and id_machinery is None:
            raise serializers.ValidationError({"id_machinery": ["Debe seleccionar una maquinaria."]})
        if is_create and id_maintenance is None:
            raise serializers.ValidationError({"id_maintenance": ["Debe seleccionar un mantenimiento."]})
        if is_create and ("usage_hours" not in attrs and "distance_km" not in attrs):
            raise serializers.ValidationError({"non_field_errors": ["Debe indicar horas de uso o distancia."]})


        if self.instance:
            proposed_usage = attrs.get("usage_hours", self.instance.usage_hours)
            proposed_distance = attrs.get("distance_km", self.instance.distance_km)

            if "usage_hours" in attrs and "distance_km" not in attrs:
                proposed_distance = None  # cambio a horas ⇒ apagamos distancia
            if "distance_km" in attrs and "usage_hours" not in attrs:
                proposed_usage = None     # cambio a distancia ⇒ apagamos horas
        else:
            proposed_usage = attrs.get("usage_hours")
            proposed_distance = attrs.get("distance_km")

        has_usage = proposed_usage is not None
        has_distance = proposed_distance is not None
        if has_usage and has_distance:
            raise serializers.ValidationError({
                "non_field_errors": ["Solo puede registrar una longitud de medida: horas o distancia (no ambas)."]
            })
        if not has_usage and not has_distance:
            raise serializers.ValidationError({
                "non_field_errors": ["Debe proporcionar al menos una medida: horas o distancia."]
            })

        # Validar existencia de FKs
        if id_machinery is not None and not Machinery.objects.filter(pk=id_machinery).exists():
            raise serializers.ValidationError({"id_machinery": ["La maquinaria no existe."]})
        if id_maintenance is not None and not Maintenance.objects.filter(pk=id_maintenance).exists():
            raise serializers.ValidationError({"id_maintenance": ["El mantenimiento no existe."]})

        # Validar duplicados 
        if id_machinery is not None and id_maintenance is not None:
            qs = PeriodicMaintenanceScheduling.objects.filter(
                machinery_id=id_machinery,
                maintenance_id=id_maintenance,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "non_field_errors": ["Ya existe un registro con ese mantenimiento para esta maquinaria."]
                })

        # guardamos en attrs los valores “propuestos” para que update/create los vean
        attrs["_proposed_usage_hours"] = proposed_usage
        attrs["_proposed_distance_km"] = proposed_distance
        return attrs

    def create(self, validated_data):
        id_machinery, id_maintenance = self._resolve_ids(validated_data)
        return PeriodicMaintenanceScheduling.objects.create(
            machinery_id=id_machinery,
            maintenance_id=id_maintenance,
            usage_hours=validated_data.get("_proposed_usage_hours"),
            distance_km=validated_data.get("_proposed_distance_km"),
        )

    def update(self, instance, validated_data):
        # FKs (opcionales en update)
        if "id_machinery" in validated_data:
            instance.machinery_id = validated_data["id_machinery"]
        if "id_maintenance" in validated_data:
            instance.maintenance_id = validated_data["id_maintenance"]

        if "_proposed_usage_hours" in validated_data or "_proposed_distance_km" in validated_data:
            instance.usage_hours = validated_data.get("_proposed_usage_hours")
            instance.distance_km = validated_data.get("_proposed_distance_km")

        instance.save()
        return instance


class PeriodicMaintenanceListSerializer(serializers.ModelSerializer):
    id_machinery = serializers.IntegerField(source="machinery_id", read_only=True)
    id_maintenance = serializers.IntegerField(source="maintenance_id", read_only=True)
    maintenance_name = serializers.CharField(source="maintenance.name", read_only=True) # trae nombre del mantenimiento

    class Meta:
        model = PeriodicMaintenanceScheduling
        fields = (
            "id_periodic_maintenance_scheduling",
            "id_machinery",
            "id_maintenance",
            "maintenance_name",
            "usage_hours",
            "distance_km",
        )