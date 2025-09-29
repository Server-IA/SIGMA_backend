from rest_framework import serializers
from machinery.models import MachineryUsageSheet


class MachineryUsageSheetDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para exponer el detalle de Uso de Maquinaria.
    """
    
    class Meta:
        model = MachineryUsageSheet
        fields = [
            'id_usage_sheet',
            'acquisition_date',
            'usage_condition',
            'usage_hours',
            'distance_value',
            'distance_unit',
            'tenancy_type',
            'is_own',
            'contract_end_date',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        """
        Custom representation to return just the IDs for foreign key relationships.
        """
        representation = super().to_representation(instance)
        
        # Get just the ID for usage_condition
        if representation.get('usage_condition'):
            representation['usage_condition'] = instance.usage_condition.id_statues
            
        # Get just the ID for distance_unit
        if representation.get('distance_unit'):
            representation['distance_unit'] = instance.distance_unit.id_units
            
        # Get just the ID for tenancy_type (can be None)
        if representation.get('tenancy_type') and instance.tenancy_type:
            representation['tenancy_type'] = instance.tenancy_type.id_types
            
        return representation
