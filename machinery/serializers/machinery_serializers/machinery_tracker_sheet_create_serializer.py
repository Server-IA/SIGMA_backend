from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import FileField
from users.models.user import User
from machinery.models import Machinery, MachineryTrackerSheet


class MachineryTrackerSheetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de la ficha de Registrar Información de Tracker.
    Campos obligatorios: id_machinery, terminal_serial_number
    """
    id_machinery = serializers.PrimaryKeyRelatedField(
        queryset=Machinery.objects.all(),
        required=True
    )

    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='id_responsible_user'
    )

    class Meta:
        model = MachineryTrackerSheet
        fields = [
            'id_machinery',
            'terminal_serial_number',
            'gps_serial_number',
            'chassis_number',
            'engine_number',
            'responsible_user'
        ]

    extra_kwargs = {
        'id_machinery': {'required': True},
        'terminal_serial_number': {'required': True}
    }

    def validate(self, data):
        """
        Validaciones de duplicados para todos los seriales.
        """
        errors = {}

        # Validar número de serie del terminal (obligatorio)
        if MachineryTrackerSheet.objects.filter(terminal_serial_number=data['terminal_serial_number']).exists():
            errors['terminal_serial_number'] = "Este número de serie de terminal ya está registrado."

        # Validar número de serie del GPS solo si no está vacío
        gps_serial = data.get('gps_serial_number', '')
        if gps_serial:
            if MachineryTrackerSheet.objects.filter(gps_serial_number=gps_serial).exists():
                errors['gps_serial_number'] = "Este número de serie de GPS ya está registrado."
        else:
            data['gps_serial_number'] = None

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """
        Crea la ficha del tracker asociada a la maquinaria.
        """
        machinery = validated_data['id_machinery']

        # Garantizar que la maquinaria no tenga ya un tracker
        if MachineryTrackerSheet.objects.filter(id_machinery=machinery).exists():
            raise serializers.ValidationError({
                "id_machinery": "Esta maquinaria ya tiene un tracker asociado."
            })

        tracker_sheet = MachineryTrackerSheet.objects.create(**validated_data)
        return tracker_sheet