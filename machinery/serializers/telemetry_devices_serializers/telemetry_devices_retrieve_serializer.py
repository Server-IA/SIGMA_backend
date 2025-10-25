from rest_framework import serializers
from machinery.models.telemetry_devices import TelemetryDevices

class TelemetryDevicesRetrieveSerializer(serializers.ModelSerializer):
    """Serializer para obtener información detallada de un dispositivo de telemetría por ID."""
    parameters = serializers.SerializerMethodField()

    def get_parameters(self, obj):
        """Obtiene los parámetros asociados al dispositivo."""
        parameters = []
        for device_parameter in obj.telemetrydeviceparameter_set.all():
            parameters.append({
                'id': device_parameter.parameter.id,
                'parameter_name': device_parameter.parameter.parameter_name,
                'avl_id_parameter': device_parameter.parameter.avl_id_parameter,
                'category': device_parameter.parameter.category
            })
        return parameters

    class Meta:
        model = TelemetryDevices
        fields = ['name', 'IMEI', 'parameters']
