import re
from rest_framework import serializers
from machinery.models.obd_faults import OBD_Faults

class OBDFaultsSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo OBD_Faults.
    Incluye todos los campos: id_obd_fault, code, description
    """
    class Meta:
        model = OBD_Faults
        fields = ['id_obd_fault', 'code', 'description']

    def validate_code(self, value):
        """
        Valida que el código OBD tenga el formato correcto: [P|C|B|U]#### (letra seguida de 4 dígitos)
        """
        if value:
            # Patrón regex para P, C, B, U seguido de exactamente 4 dígitos
            pattern = r'^[PCBU]\d{4}$'

            if not re.match(pattern, value.upper()):
                raise serializers.ValidationError(
                    "El código OBD debe tener el formato [P|C|B|U]-0000. "
                    f"El valor '{value}' no es válido."
                )

            # Normalizar a mayúsculas
            return value.upper()

        return value
