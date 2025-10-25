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
        fields = [
            'name',
            'IMEI',
            'parameters',
            'registration_date'  # Include in fields to ensure it's not updated
        ]
        read_only_fields = ['registration_date', 'id_responsible_user']  # Ensure these fields are read-only

    def validate_name(self, value):
        # Skip validation if name is not being updated
        if 'name' not in self.initial_data:
            return value
            
        if TelemetryDevices.objects.filter(name=value).exclude(id_device=self.instance.id_device).exists():
            raise serializers.ValidationError("Ya existe un dispositivo con este nombre.")
        return value

    def validate_IMEI(self, value):
        # Skip validation if IMEI is not being updated
        if 'IMEI' not in self.initial_data:
            return value
            
        if TelemetryDevices.objects.filter(IMEI=value).exclude(id_device=self.instance.id_device).exists():
            raise serializers.ValidationError("Ya existe un dispositivo con este IMEI.")
        if value < 0:
            raise serializers.ValidationError("El IMEI no puede ser negativo.")
        return value
        
    def update(self, instance, validated_data):
        # Remove registration_date from validated_data if present to prevent updates
        validated_data.pop('registration_date', None)
        
        # Handle parameters if present
        parameters = validated_data.pop('parameters', Nmone)
        
        # Update other fields
        instance = super().update(instance, validated_data)
        
        # Update parameters if provided
        if parameters is not None:
            instance.parameters.set(parameters)
            
        return instance

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

    def update(self, instance, validated_data):
        parameters = validated_data.pop('parameters', None)
        
        # Save the original registration date to restore it later
        original_registration_date = instance.registration_date
        
        with transaction.atomic():
            # Update the device fields
            instance = super().update(instance, validated_data)
            
            # Restore the original registration date
            if instance.registration_date != original_registration_date:
                instance.registration_date = original_registration_date
            
            # Only update parameters if they were provided
            if parameters is not None:
                # Delete existing parameters
                TelemetryDeviceParameter.objects.filter(telemetry_device=instance).delete()
                
                # Add new parameters
                for param_id in parameters:
                    TelemetryDeviceParameter.objects.create(
                        telemetry_device=instance,
                        parameter_id=param_id
                    )
            
            # Save with update_fields to only update specific fields
            instance.save(update_fields=['modification_date', 'registration_date'] + list(validated_data.keys()))
            
        return instance
