from rest_framework import serializers
from django.utils import timezone
from machinery.models import MachineryTrackerSheet
from users.models.user import User


class MachineryTrackerSheetUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar la información de tracker:
    - terminal_serial_number y gps_serial_number: obligatorios y únicos.
    - id_machinery: no se modifica.
    - id_responsible_user: se actualiza desde 'responsible_user' en el body.
    - modification_date: se actualiza automáticamente.
    """

    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=True,
        source='id_responsible_user'
    )

    class Meta:
        model = MachineryTrackerSheet
        fields = [
            'id_tracker_sheet',
            'terminal_serial_number',
            'gps_serial_number',
            'chassis_number',
            'engine_number',
            'responsible_user',
        ]
        read_only_fields = ['id_tracker_sheet']
        extra_kwargs = {
            'terminal_serial_number': {'required': True},
            'gps_serial_number': {'required': True},
        }

    def validate(self, data):
        """
        Validaciones: campos obligatorios y unicidad.
        """
        instance = self.instance
        errors = {}

        # Validar terminal_serial_number
        terminal_serial = data.get('terminal_serial_number', instance.terminal_serial_number)
        if not terminal_serial:
            errors['terminal_serial_number'] = "El número de serie del terminal es obligatorio."
        elif MachineryTrackerSheet.objects.filter(
            terminal_serial_number=terminal_serial
        ).exclude(id_tracker_sheet=instance.id_tracker_sheet).exists():
            errors['terminal_serial_number'] = "Este número de serie de terminal ya está registrado."

        # Validar gps_serial_number
        gps_serial = data.get('gps_serial_number', instance.gps_serial_number)
        if not gps_serial:
            errors['gps_serial_number'] = "El número de serie del GPS es obligatorio."
        elif MachineryTrackerSheet.objects.filter(
            gps_serial_number=gps_serial
        ).exclude(id_tracker_sheet=instance.id_tracker_sheet).exists():
            errors['gps_serial_number'] = "Este número de serie de GPS ya está registrado."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def update(self, instance, validated_data):
        """
        Actualiza los campos, el responsable y la fecha de modificación.
        """
        registration_date = instance.registration_date
        
        instance.terminal_serial_number = validated_data.get('terminal_serial_number', instance.terminal_serial_number)
        instance.gps_serial_number = validated_data.get('gps_serial_number', instance.gps_serial_number)
        instance.chassis_number = validated_data.get('chassis_number', instance.chassis_number)
        instance.engine_number = validated_data.get('engine_number', instance.engine_number)

        if 'id_responsible_user' in validated_data:
            instance.id_responsible_user = validated_data['id_responsible_user']

        instance.modification_date = timezone.now().date()
        
        instance.save(update_fields=[
            'terminal_serial_number',
            'gps_serial_number',
            'chassis_number',
            'engine_number',
            'id_responsible_user',
            'modification_date'
        ])
        
        if instance.registration_date != registration_date:
            instance.registration_date = registration_date
            instance.save(update_fields=['registration_date'])

        return instance
