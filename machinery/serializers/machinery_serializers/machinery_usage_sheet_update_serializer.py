from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from users.models.user import User
from machinery.models import MachineryUsageSheet
from parameterization.models import (
    Types,
    Units,
    Statues,
    TypesCategory,
    StatuesCategory,
    UnitsCategory,
)


class MachineryUsageSheetUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar la información de uso de la maquinaria (HU-MAQ-013).

    - Requiere responsible_user y justification para toda actualización
    - Valida categorías: usage_condition (cat 3), distance_unit (cat 7), tenancy_type (cat 11)
    - Valida números no negativos para usage_hours y distance_value
    - Aplica reglas de is_own: si es propia, tenancy_type y contract_end_date se limpian; si no es propia, ambos son obligatorios
    - Mantiene registration_date intacta y actualiza modification_date
    """

    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=True,
        source="id_responsible_user",
    )
    justification = serializers.CharField(required=False, allow_null=True, allow_blank=True, write_only=True)

    class Meta:
        model = MachineryUsageSheet
        fields = [
            "id_usage_sheet",
            "acquisition_date",
            "usage_condition",
            "usage_hours",
            "distance_value",
            "distance_unit",
            "tenancy_type",
            "is_own",
            "contract_end_date",
            "responsible_user",
            "justification",
        ]
        read_only_fields = ["id_usage_sheet"]
        extra_kwargs = {
            "acquisition_date": {"required": False},
            "usage_condition": {"required": False},
            "usage_hours": {"required": False},
            "distance_value": {"required": False},
            "distance_unit": {"required": False},
            "tenancy_type": {"required": False, "allow_null": True},
            "contract_end_date": {"required": False, "allow_null": True},
            "is_own": {"required": False},
        }

    def to_internal_value(self, data):
        """
        Normaliza entradas string/boolean y limpia campos cuando is_own es true.
        """
        data = data.copy()

        # Convertir is_own a booleano cuando venga como string
        is_own = data.get("is_own", None)
        if isinstance(is_own, str):
            is_own = is_own.lower() in ("true", "1")
            data["is_own"] = is_own

        # Normalizar vacíos a None
        if data.get("contract_end_date", None) == "":
            data["contract_end_date"] = None
        if data.get("tenancy_type", None) == "":
            data["tenancy_type"] = None

        # Si es propia, limpiar tenancy_type y contract_end_date si llegan
        if is_own is True:
            if "tenancy_type" in data:
                data["tenancy_type"] = None
            if "contract_end_date" in data:
                data["contract_end_date"] = None

        return super().to_internal_value(data)

    def validate_usage_hours(self, value):
        if value is None:
            raise serializers.ValidationError("Las horas de uso son obligatorias.")
        if value < 0:
            raise serializers.ValidationError("Las horas de uso no pueden ser negativas.")
        return value

    def validate_distance_value(self, value):
        if value is None:
            raise serializers.ValidationError("La distancia recorrida es obligatoria.")
        if value < 0:
            raise serializers.ValidationError("La distancia recorrida no puede ser negativa.")
        return value

    def validate_usage_condition(self, value):
        # Cat 3: estados de uso de la maquinaria
        if value.id_statues_categories_id != 3:
            expected = StatuesCategory.objects.filter(id_statues_categories=3).first()
            expected_name = expected.name if expected else "Categoría 3"
            raise ValidationError(
                f"El estado de uso debe pertenecer a la categoría '{expected_name}'."
            )
        return value

    def validate_distance_unit(self, value):
        # Cat 7: unidades de longitud
        if value.id_units_categories_id != 7:
            expected = UnitsCategory.objects.filter(id_units_categories=7).first()
            expected_name = expected.name if expected else "Categoría 7"
            raise ValidationError(
                f"La unidad de distancia debe pertenecer a la categoría '{expected_name}'."
            )
        return value

    def validate_tenancy_type(self, value):
        # Cat 11: tipos de tenencia
        if value and value.id_types_categories_id != 11:
            expected = TypesCategory.objects.filter(id_types_categories=11).first()
            expected_name = expected.name if expected else "Categoría 11"
            raise ValidationError(
                f"El tipo de tenencia debe pertenecer a la categoría '{expected_name}'."
            )
        return value

    def validate(self, data):
        instance = self.instance
        if not instance:
            return data

        # is_own efectivo: nuevo valor si llega, o el que ya tiene
        is_own = data.get("is_own", instance.is_own)

        if is_own:
            # En maquinaria propia no debe quedar tenencia ni fin de contrato
            if "tenancy_type" in data:
                data["tenancy_type"] = None
            if "contract_end_date" in data:
                data["contract_end_date"] = None
        else:
            tenancy = data.get("tenancy_type", instance.tenancy_type)
            contract = data.get("contract_end_date", instance.contract_end_date)
            if tenancy is None:
                raise ValidationError({
                    "tenancy_type": "El tipo de tenencia es obligatorio cuando la maquinaria no es propia."
                })
            if contract is None or str(contract) == "":
                raise ValidationError({
                    "contract_end_date": "La fecha fin de contrato es obligatoria cuando la maquinaria no es propia."
                })

        # Regla de justificación: solo en PUT cuando la maquinaria asociada no esté en estado 3
        request = self.context.get('request')
        if request and request.method == 'PUT':
            machinery = getattr(instance, 'id_machinery', None)
            if machinery and getattr(machinery, 'machinery_operational_status', None):
                if machinery.machinery_operational_status.id_statues != 3:
                    justification = data.get('justification')
                    if not justification:
                        status_3_name = Statues.objects.get(id_statues=3).name
                        raise ValidationError({
                            'justification': f"La justificación es obligatoria cuando la maquinaria no está en estado '{status_3_name}'. Estado actual: '{machinery.machinery_operational_status.name}'"
                        })

        return data

    def update(self, instance, validated_data):
        # Obtener la justificación antes de sacarla de validated_data
        justification = validated_data.pop("justification", None)
        
        registration_date = instance.registration_date

        # Asignar campos presentes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Actualizar modification_date
        instance.modification_date = timezone.now().date()
        
        # Asignar la justificación al modelo si existe
        if justification is not None:
            instance.justification = justification

        # Guardar únicamente campos provistos + auditables + justificación
        update_fields = set(list(validated_data.keys()) + ["modification_date", "id_responsible_user"])
        if justification is not None:
            update_fields.add("justification")
            
        instance.save(update_fields=list(update_fields))

        # Restaurar registration_date si cambió por auto_now
        if instance.registration_date != registration_date:
            instance.registration_date = registration_date
            instance.save(update_fields=["registration_date"])

        return instance


