from rest_framework import serializers
from maintenance.models import MaintenanceSpareParts


class MaintenanceSparePartsListSerializer(serializers.ModelSerializer):
    """
    Serializador para listar repuestos de mantenimiento con información de la marca.
    """
    
    # Información de la marca
    brand_name = serializers.CharField(source='spare_part_brand.name', read_only=True)
    brand_id = serializers.IntegerField(source='spare_part_brand.id_brands', read_only=True)

    class Meta:
        model = MaintenanceSpareParts
        fields = [
            'id_maintenance_spare_parts',
            'name',
            'spare_parts_cost',
            'brand_id',
            'brand_name'
        ]
