from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from datetime import date

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

        # Convertir is_own string -> bool
        if "is_own" in data and isinstance(data["is_own"], str):
            data["is_own"] = data["is_own"].lower() in ("true", "1")

        # Normalizar campos vacíos a None
        if data.get("contract_end_date") == "":
            data["contract_end_date"] = None
        if data.get("tenancy_type") == "":
            data["tenancy_type"] = None

        # Si es propia, limpiar valores
        if data.get("is_own") is True:
            data["tenancy_type"] = None
            data["contract_end_date"] = None

        return super().to_internal_value(data)

    # ----------------------------
    # Validaciones de campos
    # ----------------------------
    def validate_usage_hours(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Las horas de uso no pueden ser negativas.")
        return value

    def validate_distance_value(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("La distancia recorrida no puede ser negativa.")
        return value

    def validate_usage_condition(self, value):
        if value.id_statues_categories_id != 3:
            cat = StatuesCategory.objects.filter(id_statues_categories=3).first()
            raise ValidationError(
                f"El estado de uso debe pertenecer a la categoría '{cat.name if cat else 'Categoría 3'}'."
            )
        return value

    def validate_distance_unit(self, value):
        if value.id_units_categories_id != 7:
            cat = UnitsCategory.objects.filter(id_units_categories=7).first()
            raise ValidationError(
                f"La unidad de distancia debe pertenecer a la categoría '{cat.name if cat else 'Categoría 7'}'."
            )
        return value

    def validate_tenancy_type(self, value):
        if value and value.id_types_categories_id != 11:
            cat = TypesCategory.objects.filter(id_types_categories=11).first()
            raise ValidationError(
                f"El tipo de tenencia debe pertenecer a la categoría '{cat.name if cat else 'Categoría 11'}'."
            )
        return value

    # ----------------------------
    # Validación general
    # ----------------------------
    def validate(self, data):
        instance = self.instance
        if not instance:
            return data

        # Valor final efectivo de is_own
        is_own = data.get("is_own", instance.is_own)

        acquisition_date = data.get("acquisition_date", instance.acquisition_date)
        contract_end = data.get("contract_end_date", instance.contract_end_date)
        tenancy_type = data.get("tenancy_type", instance.tenancy_type)

        # -------------------------------------------------
        #  Validación del BUG: fechas incoherentes
        # -------------------------------------------------
        if not is_own:
            if tenancy_type is None:
                raise ValidationError({
                    "tenancy_type": "El tipo de tenencia es obligatorio cuando la maquinaria no es propia."
                })

            if contract_end is None:
                raise ValidationError({
                    "contract_end_date": "La fecha fin de contrato es obligatoria cuando la maquinaria no es propia."
                })

            # Fecha fin < fecha adquisición
            if acquisition_date and contract_end and contract_end < acquisition_date:
                raise ValidationError({
                    "contract_end_date": "La fecha fin de contrato no puede ser anterior a la fecha de adquisición."
                })

            # Fecha fin < hoy
            if contract_end and contract_end < date.today():
                raise ValidationError({
                    "contract_end_date": "La fecha fin de contrato no puede ser anterior a la fecha actual."
                })

        # -------------------------------------------------
        # Reglas de justificación
        # -------------------------------------------------
        request = self.context.get("request")
        if request and request.method == "PUT":
            machinery = getattr(instance, "id_machinery", None)
            status = getattr(machinery, "machinery_operational_status", None)

            # Si tiene estado y NO es 3 → justificación obligatoria
            if status and status.id_statues != 3:
                if not data.get("justification"):
                    raise ValidationError({
                        "justification": (
                            f"La justificación es obligatoria porque la maquinaria "
                            f"está en estado '{status.name}', no en 'Operativo (3)'."
                        )
                    })

        return data

    def update(self, instance, validated_data):
        # Obtener la justificación antes de sacarla de validated_data
        justification = validated_data.pop("justification", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Actualizar modification_date
        instance.modification_date = timezone.now().date()
        
        # Asignar la justificación al modelo si existe
        if justification is not None:
            instance.justification = justification

        instance.save()

        return instance
