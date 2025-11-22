from rest_framework import serializers
from payroll.models import EmployeeContract
from parameterization.models import Types


class EmployeeContractTerminateSerializer(serializers.Serializer):
    """
    Serializer para finalizar un contrato de empleado.
    """
    contract_termination_reason = serializers.IntegerField(required=True)
    observation = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    def validate_contract_termination_reason(self, value):
        """
        Valida que el motivo de finalización pertenezca a la categoría 20.
        """
        try:
            termination_reason = Types.objects.select_related('id_types_categories').get(pk=value)
        except Types.DoesNotExist:
            raise serializers.ValidationError(
                f"El motivo de finalización con ID {value} no existe."
            )
        
        # Validar que pertenezca a la categoría 20
        if termination_reason.id_types_categories_id != 20:
            raise serializers.ValidationError(
                f"El motivo de finalización debe pertenecer a la categoría 20. "
                f"El tipo seleccionado pertenece a la categoría {termination_reason.id_types_categories_id}."
            )
        
        return value

    def validate_observation(self, value):
        """
        Valida que la observación no sea solo espacios en blanco.
        """
        if value is not None:
            value = value.strip()
            if not value:
                return None
        return value

