from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from machinery.models import SpecificTechnicalSheet, Machinery
from parameterization.models import Types, Units, Statues, TypesCategory
from users.models.user import User
from django.utils import timezone

class SpecificTechnicalSheetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de la ficha técnica específica de maquinaria.
    """

    # FK hacia maquinaria
    id_machinery = serializers.PrimaryKeyRelatedField(
        queryset=Machinery.objects.all()
    )

    # Validaciones para campos clave
    power_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(), required=True
    )
    engine_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(), required=True
    )
    cylinder_capacity_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(), required=True
    )
    cylinder_arrangement_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(), required=True
    )
    fuel_consumption_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(), required=True
    )
    transmission_system_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(), required=True
    )
    operating_weight_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(), required=True
    )
    max_speed_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(), required=True
    )
    dimension_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(), required=True
    )
    net_weight_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(), required=True
    )


    class Meta:
        model = SpecificTechnicalSheet
        fields = "__all__"
        extra_kwargs = {
            "power": {"required": True},
            "engine_type": {"required": True},
            "cylinder_capacity": {"required": True},
            "cylinder_arrangement_type": {"required": True},
            "cylinder_count": {"required": True},
            "fuel_consumption": {"required": True},
            "transmission_system_type": {"required": True},
            "operating_weight": {"required": True},
            "max_speed": {"required": True},
            "width": {"required": True},
            "length": {"required": True},
            "height": {"required": True},
            "net_weight": {"required": True},
            "id_machinery": {"required": True},
        }

    def validate(self, data):
        """
        Validaciones adicionales de negocio.
        """
        # Potencia positiva
        if data.get("power") is not None and data["power"] <= 0:
            raise ValidationError({"power": "La potencia debe ser un valor positivo."})

        # Peso operativo obligatorio
        if not data.get("operating_weight"):
            raise ValidationError({"operating_weight": "Debe indicar el peso operativo."})

        # Velocidad máxima mayor que cero
        if data.get("max_speed") is not None and data["max_speed"] <= 0:
            raise ValidationError({"max_speed": "La velocidad máxima debe ser mayor que cero."})

        if data.get("cylinder_count") is not None and data["cylinder_count"] <= 0:
            raise ValidationError({"cylinder_count": "El número de cilindros debe ser mayor que 0."})

        for field in ["width", "length", "height"]:
            if data.get(field) is not None and data[field] <= 0:
                raise ValidationError({field: f"{field} debe ser mayor que 0."})

        if data.get("carrying_capacity") is not None and data["carrying_capacity"] < 0:
            raise ValidationError({"carrying_capacity": "La capacidad de carga no puede ser negativa."})

        if data.get("performance_rpm_min") and data.get("performance_rpm_max"):
            if data["performance_rpm_min"] >= data["performance_rpm_max"]:
                raise ValidationError({"performance_rpm": "El valor mínimo de RPM debe ser menor que el máximo."})

        return data

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("La descripción no puede estar vacía.")
        if len(value) < 10:
            raise serializers.ValidationError("La descripción debe contener al menos 10 caracteres.")
        return value

    def create(self, validated_data):
        """
        Crea la ficha técnica específica asociada a una maquinaria.
        """
        try:
            validated_data['machinery_operational_status'] = operational_status
            machinery = validated_data["id_machinery"]
            machinery.machinery_operational_status = operational_status
            machinery.save(update_fields=["machinery_operational_status"])

            sheet = SpecificTechnicalSheet.objects.create(**validated_data)
            return sheet

        except Exception as e:
            raise serializers.ValidationError({"error": f"Error al crear la ficha técnica específica: {str(e)}"})
