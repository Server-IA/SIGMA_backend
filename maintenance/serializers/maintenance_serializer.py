from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from maintenance.models import Maintenance
from parameterization.models import Types, Statues, TypesCategory
from users.models.user import User

class MaintenanceSerializer(serializers.ModelSerializer):
    # Campo para el usuario responsable
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='id_responsible_user',
        error_messages={
            "does_not_exist": "El usuario responsable no existe.",
            "required": "El usuario responsable es obligatorio."
        }
    )

    # Campo para el tipo de mantenimiento
    maintenance_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(),
        error_messages={
            "does_not_exist": "El tipo de mantenimiento seleccionado no existe.",
            "required": "El tipo de mantenimiento es obligatorio."
        }
    )

    # Campos básicos
    name = serializers.CharField(
        max_length=100,
        error_messages={
            "blank": "El nombre es obligatorio.",
            "max_length": "El nombre no puede exceder 100 caracteres.",
        },
    )

    description = serializers.CharField(
        max_length=300,
        trim_whitespace=True,
        error_messages={
            "max_length": "La descripción no puede exceder 300 caracteres.",
            "blank": "La descripción es obligatoria.",
            "required": "La descripción es obligatoria.",
        }
    )

    # Campo de solo lectura para el estado de mantenimiento
    maintenance_status = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=1  # Este valor será manejado en el método create
    )

    class Meta:
        model = Maintenance
        fields = [
            'id_maintenance',
            'name',
            'description',
            'maintenance_type',
            'maintenance_status',
            'responsible_user',
            'registration_date',
            'modification_date',
        ]
        read_only_fields = ('id_maintenance', 'registration_date', 'modification_date', 'maintenance_status')

    def validate_maintenance_type(self, value):
        """
        Valida que el tipo de mantenimiento pertenezca a la categoría con id=12.
        """
        if value.id_types_categories_id != 12:
            from parameterization.models import TypesCategory
            expected_category = TypesCategory.objects.get(id_types_categories=12)
            raise serializers.ValidationError(
                f"El tipo de mantenimiento debe pertenecer a la categoría '{expected_category.name}'."
            )
        return value

    def validate_name(self, value):
        value = value.strip()
        # Obtener la instancia actual si existe (para actualización)
        instance = getattr(self, 'instance', None)
        # Verificar si existe otro mantenimiento con el mismo nombre (excluyendo la instancia actual)
        qs = Maintenance.objects.filter(name__iexact=value)
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un mantenimiento con este nombre.")
        return value

    def validate_maintenance_type(self, value):
        """
        Valida que el tipo de mantenimiento pertenezca a la categoría con id 12.
        """
        if value.id_types_categories_id != 12:
            expected_category = TypesCategory.objects.get(id_types_categories=12)
            raise serializers.ValidationError(
                f"El tipo de mantenimiento debe pertenecer a la categoría '{expected_category.name}'."
            )
        return value

    def create(self, validated_data):
        """
        Crea una nueva instancia de mantenimiento.
        """
        default_status = Statues.objects.get(id_statues=1)
        instance = Maintenance.objects.create(
            **validated_data,
            maintenance_status=default_status
        )
        return instance

def update(self, instance, validated_data):
    """
    Actualiza una instancia existente de mantenimiento.
    Actualiza automáticamente la fecha de modificación.
    """
    if 'name' in validated_data:
        name = validated_data['name'].strip()
        if Maintenance.objects.filter(name__iexact=name).exclude(pk=instance.pk).exists():
            raise serializers.ValidationError({
                'name': 'Ya existe un mantenimiento con este nombre.'
            })
        instance.name = name

    if 'description' in validated_data:
        instance.description = validated_data['description'].strip()

    if 'maintenance_type' in validated_data:
        maintenance_type = validated_data['maintenance_type']
        if maintenance_type.id_types_categories_id != 12:
            expected_category = TypesCategory.objects.get(id_types_categories=12)
            raise serializers.ValidationError({
                'maintenance_type': f"El tipo de mantenimiento debe pertenecer a la categoría '{expected_category.name}'."
            })
        instance.maintenance_type = maintenance_type

    if 'id_responsible_user' in validated_data:
        try:
            instance.id_responsible_user = validated_data['id_responsible_user']
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'responsible_user': 'El usuario responsable no existe.'
            })

    instance.save()

    return instance