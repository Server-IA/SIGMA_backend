from rest_framework import serializers
from django.db import transaction
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.parameters import Parameters
from machinery.models.telemetry_device_parameter import TelemetryDeviceParameter

class TelemetryDevicesUpdateSerializer(serializers.ModelSerializer):
    parameters = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        help_text="Lista de IDs de parámetros a asociar"
    )

    class Meta:
        model = TelemetryDevices
        fields = ['name', 'IMEI', 'parameters']

    def validate_name(self, value):
        # Solo validar que no esté vacío
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre es requerido.")

        # Verificar que no se repita con otros dispositivos (excluyendo el actual)
        existing_device = TelemetryDevices.objects.filter(name=value.strip()).exclude(id_device=self.instance.id_device)
        if existing_device.exists():
            raise serializers.ValidationError("Ya existe otro dispositivo con este nombre.")

        return value.strip()

    def validate_IMEI(self, value):
        # Solo validar que no sea negativo
        if value < 0:
            raise serializers.ValidationError("El IMEI no puede ser negativo.")

        # Verificar que no se repita con otros dispositivos (excluyendo el actual)
        existing_device = TelemetryDevices.objects.filter(IMEI=value).exclude(id_device=self.instance.id_device)
        if existing_device.exists():
            raise serializers.ValidationError("Ya existe otro dispositivo con este IMEI.")

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
    def update(self, instance, validated_data):
        parameters = validated_data.pop('parameters', [])

        # Actualizar campos del dispositivo
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Eliminar parámetros anteriores
        TelemetryDeviceParameter.objects.filter(telemetry_device=instance).delete()

        # Crear nuevos parámetros
        for param_id in parameters:
            TelemetryDeviceParameter.objects.create(
                telemetry_device=instance,
                parameter_id=param_id
            )

        # Solo actualizar modification_date (registration_date y id_responsible_user se mantienen igual)
        instance.save(update_fields=['name', 'IMEI', 'modification_date'])

        return instance
