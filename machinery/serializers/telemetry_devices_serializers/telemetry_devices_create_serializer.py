from rest_framework import serializers
from django.db import transaction
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.parameters import Parameters
from machinery.models.telemetry_device_parameter import TelemetryDeviceParameter
from users.models import User

class TelemetryDevicesCreateSerializer(serializers.ModelSerializer):
    parameters = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="Lista de IDs de parámetros a asociar"
    )

    class Meta:
        model = TelemetryDevices
        fields = [
            'name',
            'IMEI',
            'parameters',
        ]
        read_only_fields = ['registration_date', 'modification_date']

    def validate_name(self, value):
        if TelemetryDevices.objects.filter(name=value).exists():
            raise serializers.ValidationError("Ya existe un dispositivo con este nombre.")
        return value

    def validate_IMEI(self, value):
        if TelemetryDevices.objects.filter(IMEI=value).exists():
            raise serializers.ValidationError("Ya existe un dispositivo con este IMEI.")
        if value < 0:
            raise serializers.ValidationError("El IMEI no puede ser negativo.")
        return value

    def validate_parameters(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("Debe seleccionar al menos un parámetro.")
        
        unique_params = list(dict.fromkeys(value))
        if len(unique_params) != len(value):
            raise serializers.ValidationError("La lista de parámetros contiene duplicados.")
        
        for param_id in unique_params:
            if not Parameters.objects.filter(id=param_id).exists():
                raise serializers.ValidationError(f"El parámetro con ID {param_id} no existe.")
        return unique_params

    @transaction.atomic
    def create(self, validated_data):
        parameters = validated_data.pop('parameters')
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Usuario no autenticado.")
        
        try:
            user = User.objects.get(id_user=request.user.id)
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario responsable no encontrado.")
        
        validated_data['id_statues_id'] = 1
        validated_data['id_responsible_user'] = user

        telemetry_device = TelemetryDevices.objects.create(**validated_data)

        for param_id in parameters:
            TelemetryDeviceParameter.objects.create(
                telemetry_device=telemetry_device,
                parameter_id=param_id
            )

        return telemetry_device
