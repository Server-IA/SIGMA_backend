from rest_framework import serializers
from maintenance.models import Maintenance

class MaintenanceListSerializer(serializers.ModelSerializer):
    """
    Serializador para listar mantenimientos con información básica y estado.
    """
    estado = serializers.CharField(source='maintenance_status.name', read_only=True)
    id_estado = serializers.IntegerField(source='maintenance_status.id_statues', read_only=True)
    
    tipo_mantenimiento = serializers.CharField(source='maintenance_type.name', read_only=True)
    id_tipo_mantenimiento = serializers.IntegerField(source='maintenance_type.id_types', read_only=True)

    class Meta:
        model = Maintenance
        fields = [
            'id_maintenance',
            'name',
            'description',
            'id_estado',
            'estado',
            'id_tipo_mantenimiento',
            'tipo_mantenimiento'
        ]
