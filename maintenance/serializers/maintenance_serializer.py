from rest_framework import serializers
from maintenance.models import Maintenance

class MaintenanceSerializer(serializers.ModelSerializer):
    # Exponer el ID del responsable como entero
    id_responsible_user = serializers.IntegerField(source='id_responsible_user_id', read_only=True)
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
    },
    
    )

    class Meta:
        model = Maintenance
        fields = [
            'id_maintenance',
            'name',
            'description',
            'maintenance_type',
            'maintenance_status',
            'id_responsible_user',
            'registration_date',
            'modification_date',
        ]
        read_only_fields = ('id_maintenance', 'id_responsible_user', 'registration_date', 'modification_date')

    def validate_name(self, value):
        value = value.strip()
        if Maintenance.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un mantenimiento con este nombre.")
        return value