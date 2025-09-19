from rest_framework import serializers
from machinery.models.machinery import Machinery
from parameterization.models import Types, Models, Statues
from users.models.user import User
from django.utils import timezone


class MachineryGeneralSheetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de la ficha general de maquinaria.
    Campos obligatorios: machinery_name, serial_number, machinery_type, id_model, machinery_secondary_type
    """
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )

    machinery_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(),
        source = 'id_machinery_type'
    )

    id_model = serializers.PrimaryKeyRelatedField(
        queryset=Models.objects.all(),
        source = 'id_model'
    )

    machinery_secondary_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(),
        source = 'id_machinery_secondary_type'
    )

    class Meta:
        model = Machinery
        fields = [
            'machinery_name',
            'serial_number',
            'machinery_type',
            'id_model',
            'machinery_secondary_type',
            'manufacturing_year',
            'tariff_subheading',
            'image_path',
            'responsible_user',
        ]
        extra_kwargs = {
            'machinery_name': {'required': True},
            'serial_number': {'required': True},
        }

    def validate_machinery_name(self, value):
        """
        Validar que el nombre de la maquinaria no exista en la base de datos
        """
        if Machinery.objects.filter(machinery_name=value).exists():
            raise serializers.ValidationError("Ya existe una máquina con este nombre.")
        return value

    def validate_manufacturing_year(self, value):
        """
        Valida que el año de fabricación sea válido.
        """
        current_year = timezone.now().year

        if value is not None:
            if value > current_year:
                raise serializers.ValidationError(
                    "El año de fabricación no puede ser mayor al año actual."
                )
            if value < 1900:
                raise serializers.ValidationError(
                    "El año de fabricación debe ser posterior a 1900."
                )
        return value

    def validate_serial_number(self, value):
        """
        Validar que el número de serie no exista en la base de datos
        """
        if Machinery.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError("Ya existe una máquina con este número de serie.")
        return value

    def validate_id_device(self, value):
        """
        Valida que el dispositivo de telemetría no esté siendo usado por otra máquina.
        """
        if value:  # Solo validar si se proporciona un dispositivo
            if Machinery.objects.filter(id_device=value).exists():
                raise serializers.ValidationError(
                    "Este dispositivo de telemetría ya está siendo utilizado por otra máquina."
                )
        return value

    def create(self, validated_data):
        """
        Crea una nueva instancia de maquinaria con el estado operativo por defecto (id=3) que indica "En Registro".
        """
        try:
            operational_status = Statues.objects.get(id_statues=3)
        except Statues.DoesNotExist:
            raise serializers.ValidationError({"error": "No se encontró el estado requerido"})

        machinery = Machinery.objects.create(
            machinery_operational_status=operational_status,
            **validated_data
        )

        return machinery