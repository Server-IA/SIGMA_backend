from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from machinery.models import SpecificTechnicalSheet, Machinery
from parameterization.models import Statues
from parameterization.models import Types, Units, Statues, TypesCategory
from parameterization.models.units_category import UnitsCategory
from users.models.user import User

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
        queryset=Units.objects.all()
    )
    engine_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )
    cylinder_capacity_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    cylinder_arrangement_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )
    traction_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )
    fuel_consumption_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    transmission_system_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )
    operating_weight_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    max_speed_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    draft_force_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    maximum_altitude_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    performance_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    dimension_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    net_weight_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )

    air_conditioning_system_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )
    air_conditioning_system_consumption_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    maximum_working_pressure_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    pump_flow_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    hydraulic_tank_capacity_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    emission_level_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )
    cabin_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all()
    )
    fuel_capacity_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )
    carrying_capacity_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all()
    )

    def validate(self, attrs):
        """
        Validación personalizada para asegurar que no exista ya una hoja técnica para esta máquina.
        """
        id_machinery = attrs.get('id_machinery')
        
        if id_machinery and SpecificTechnicalSheet.objects.filter(id_machinery=id_machinery).exists():
            raise serializers.ValidationError({
                'id_machinery': 'Ya existe una hoja técnica específica para esta máquina.'
            })

        return attrs


    class Meta:
        model = SpecificTechnicalSheet
        fields = [
            # Motor y transmisión
            "power",
            "power_unit",
            "engine_type",
            "cylinder_capacity",
            "cylinder_capacity_unit",
            "cylinder_arrangement_type",
            "cylinder_count",
            "traction_type",
            "fuel_consumption",
            "fuel_consumption_unit",
            "transmission_system_type",

            # Capacidad y rendimiento
            "fuel_capacity",
            "fuel_capacity_unit",
            "carrying_capacity",
            "carrying_capacity_unit",
            "operating_weight",
            "operating_weight_unit",
            "max_speed",
            "max_speed_unit",
            "draft_force",
            "draft_force_unit",
            "maximum_altitude",
            "maximum_altitude_unit",
            "minimum_performance",
            "maximum_performance",
            "performance_unit",

            # Dimensiones y peso
            "width",
            "length",
            "height",
            "dimension_unit",
            "net_weight",
            "net_weight_unit",

            # Sistemas auxiliares e hidráulicos
            "air_conditioning_system_type",
            "air_conditioning_system_consumption",
            "air_conditioning_system_consumption_unit",
            "maximum_working_pressure",
            "maximum_working_pressure_unit",
            "pump_flow",
            "pump_flow_unit",
            "hydraulic_tank_capacity",
            "hydraulic_tank_capacity_unit",

            # Normatividad y seguridad
            "emission_level_type",
            "cabin_type",

            # Relación con la máquina
            "id_machinery",

            # Responsable
            "id_responsible_user",
            # justificación
            "justification",
        ]
        extra_kwargs = {
            "power": {"required": True},
            "power_unit": {"required": True},
            "engine_type": {"required": True},
            "cylinder_capacity": {"required": True},
            "cylinder_capacity_unit": {"required": True},
            "cylinder_arrangement_type": {"required": True},
            "cylinder_count": {"required": True},
            "fuel_consumption": {"required": True},
            "fuel_consumption_unit": {"required": True},
            "transmission_system_type": {"required": True},
            "operating_weight": {"required": True},
            "operating_weight_unit": {"required": True},
            "max_speed": {"required": True},
            "max_speed_unit": {"required": True},
            "width": {"required": True},
            "length": {"required": True},
            "height": {"required": True},
            "dimension_unit": {"required": True},
            "net_weight": {"required": True},
            "net_weight_unit": {"required": True},
            "id_machinery": {"required": True},
            "id_responsible_user": {"required": True},
        }

    justification = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate(self, data):
        """
        Validaciones adicionales de negocio y de categorías.
        """

        # === Validaciones de negocio ===
        if data.get("power") is not None and data["power"] <= 0:
            raise ValidationError({"power": "La potencia debe ser un valor positivo."})

        if not data.get("operating_weight"):
            raise ValidationError({"operating_weight": "Debe indicar el peso operativo."})

        if data.get("max_speed") is not None and data["max_speed"] <= 0:
            raise ValidationError({"max_speed": "La velocidad máxima debe ser mayor que cero."})

        if data.get("cylinder_count") is not None and data["cylinder_count"] <= 0:
            raise ValidationError({"cylinder_count": "El número de cilindros debe ser mayor que 0."})

        for field in ["width", "length", "height"]:
            if data.get(field) is not None and data[field] <= 0:
                raise ValidationError({field: f"{field} debe ser mayor que 0."})

        if data.get("carrying_capacity") is not None and data["carrying_capacity"] < 0:
            raise ValidationError({"carrying_capacity": "La capacidad de carga no puede ser negativa."})

        if data.get("minimum_performance") and data.get("maximum_performance"):
            if data["minimum_performance"] >= data["maximum_performance"]:
                raise ValidationError({
                    "performance": "El rendimiento mínimo debe ser menor que el máximo."
                })

        # === Validación de Unidades ===
        unit_category_map = {
            "power_unit": 1,  # Potencia
            "cylinder_capacity_unit": 2,  # Capacidad de cilindro
            "fuel_capacity_unit": 2,  # Capacidad de combustible
            "hydraulic_tank_capacity_unit": 2,  # Capacidad hidráulica
            "pump_flow_unit": 3,  # Caudal/Consumo
            "fuel_consumption_unit": 3,  # Caudal/Consumo
            "air_conditioning_system_consumption_unit": 3,  # Caudal/Consumo
            "carrying_capacity_unit": 4,  # Capacidad de carga
            "operating_weight_unit": 4,  # Peso operativo
            "net_weight_unit": 4,  # Peso neto
            "max_speed_unit": 5,  # Velocidad
            "draft_force_unit": 6,  # Fuerza
            "maximum_altitude_unit": 7,  # Altitud
            "dimension_unit": 7,  # Dimensiones
            "performance_unit": 8,  # Rendimiento - Frecuencia / Velocidad angular
            "maximum_working_pressure_unit": 9,  # Presión
        }

        # Coerción: operating_weight es CharField en el modelo
        if data.get("operating_weight") is not None and not isinstance(data.get("operating_weight"), str):
            try:
                data["operating_weight"] = str(data["operating_weight"])
            except Exception:
                raise ValidationError({"operating_weight": "Valor inválido para operating_weight."})

        # === Unicidad: una sola ficha por maquinaria ===
        # Permite actualizar la misma instancia sin disparar el error
        id_machinery = data.get("id_machinery")
        if id_machinery is not None:
            qs = SpecificTechnicalSheet.objects.filter(id_machinery=id_machinery)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({
                    "id_machinery": "Ya existe una hoja técnica específica para esta máquina."
                })

        for field, expected_category in unit_category_map.items():
            if field in data and data[field]:
                unit = data[field]
                if unit.id_units_categories_id != expected_category:
                    # Usar UnitsCategory para nombres de categorías de unidades
                    expected_category_obj = UnitsCategory.objects.filter(id_units_categories=expected_category).first()
                    # Intentar obtener también el nombre de la categoría actual de la unidad
                    current_category_obj = UnitsCategory.objects.filter(id_units_categories=unit.id_units_categories_id).first()
                    if expected_category_obj is None:
                        raise ValidationError({
                            field: (
                                f"La unidad '{unit.name}' no es válida para este campo. "
                                f"Se requiere una unidad de la categoría con ID '{expected_category}', "
                                f"pero esa categoría no existe en el catálogo."
                            )
                        })
                    raise ValidationError({
                        field: (
                            f"La unidad '{unit.name}' (categoría actual: "
                            f"'{current_category_obj.name}'" if current_category_obj else f"ID {unit.id_units_categories_id}"
                            f") no es válida para este campo. "
                            f"Se requiere una unidad de la categoría '{expected_category_obj.name}'."
                        )
                    })

        # === Validación de Tipos ===
        type_category_map = {
            "engine_type": 4,  # Motores
            "cylinder_arrangement_type": 5,  # Disposición de cilindraje
            "traction_type": 6,  # Tracciones
            "transmission_system_type": 7,  # Sistemas de transmisión
            "air_conditioning_system_type": 8,  # Aire acondicionado
            "emission_level_type": 9,  # Niveles de emisión
            "cabin_type": 10,  # Cabinas
        }

        for field, expected_category in type_category_map.items():
            if field in data and data[field]:
                type_obj = data[field]
                if type_obj.id_types_categories_id != expected_category:
                    expected_category_obj = TypesCategory.objects.filter(id_types_categories=expected_category).first()
                    if expected_category_obj is None:
                        raise ValidationError({
                            field: (
                                f"El tipo '{type_obj.name}' no es válido para este campo. "
                                f"Se requiere un tipo de la categoría con ID '{expected_category}', "
                                f"pero esa categoría no existe en el catálogo."
                            )
                        })
                    raise ValidationError({
                        field: (
                            f"El tipo '{type_obj.name}' no es válido para este campo. "
                            f"Se requiere un tipo de la categoría '{expected_category_obj.name}'."
                        )
                    })

        return data

    def create(self, validated_data):
        """
        Crea la ficha técnica específica asociada a una maquinaria.
        """
        try:
            machinery = validated_data["id_machinery"]
            machinery.save(update_fields=["machinery_operational_status"])

            sheet = SpecificTechnicalSheet.objects.create(**validated_data)
            return sheet

        except Exception as e:
            raise serializers.ValidationError({"error": f"Error al crear la ficha técnica específica: {str(e)}"})

    def update(self, instance, validated_data):
        """
        Reutiliza las validaciones existentes y exige justificación en PUT si la maquinaria asociada no está en estado 3.
        """
        request = self.context.get('request')
        if request and request.method == 'PUT':
            machinery = instance.id_machinery
            if machinery and machinery.machinery_operational_status_id and machinery.machinery_operational_status.id_statues != 3:
                if not validated_data.get('justification'):
                    status_3_name = Statues.objects.get(id_statues=3).name
                    raise serializers.ValidationError({
                        'justification': f"La justificación es obligatoria cuando la maquinaria no está en estado '{status_3_name}'. Estado actual: '{machinery.machinery_operational_status.name}'"
                    })
        return super().update(instance, validated_data)
