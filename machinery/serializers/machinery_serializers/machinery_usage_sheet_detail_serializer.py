from rest_framework import serializers
from machinery.models import MachineryUsageSheet
from parameterization.models.statues import Statues
from parameterization.models.units import Units
from parameterization.models.types import Types


class MachineryUsageSheetDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para exponer el detalle de Uso de Maquinaria.
    Incluye los nombres de los campos relacionados además de sus IDs.
    """
    # Campos de solo lectura para los nombres
    usage_condition_name = serializers.SerializerMethodField()
    distance_unit_name = serializers.SerializerMethodField()
    tenancy_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MachineryUsageSheet
        fields = [
            'id_usage_sheet',
            'acquisition_date',
            'usage_condition', 'usage_condition_name',
            'usage_hours',
            'distance_value',
            'distance_unit', 'distance_unit_name',
            'tenancy_type', 'tenancy_type_name',
            'is_own',
            'contract_end_date',
        ]
        read_only_fields = fields

    def get_usage_condition_name(self, obj):
        return obj.usage_condition.name if obj.usage_condition else None
    
    def get_distance_unit_name(self, obj):
        return obj.distance_unit.name if obj.distance_unit else None
    
    def get_tenancy_type_name(self, obj):
        return obj.tenancy_type.name if obj.tenancy_type else None

    def to_representation(self, instance):
        """
        Custom representation to include both IDs and names for related fields.
        """
        representation = super().to_representation(instance)
        
        # Get ID for usage_condition
        if representation.get('usage_condition'):
            representation['usage_condition'] = instance.usage_condition.id_statues
            
        # Get ID for distance_unit
        if representation.get('distance_unit'):
            representation['distance_unit'] = instance.distance_unit.id_units
            
        # Get just the ID for tenancy_type (can be None)
        if representation.get('tenancy_type') and instance.tenancy_type:
            representation['tenancy_type'] = instance.tenancy_type.id_types
            
        return representation
