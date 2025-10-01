from rest_framework import serializers
from maintenance.models import MaintenanceSpareParts


class MaintenanceSparePartsListSerializer(serializers.ModelSerializer):
    """
    Serializador para listar repuestos de mantenimiento con información de la marca.
    """
    
    # Información de la marca
    brand_name = serializers.CharField(source='spare_part_brand.name', read_only=True)
    brand_id = serializers.IntegerField(source='spare_part_brand.id_brands', read_only=True)
    brand_description = serializers.CharField(source='spare_part_brand.description', read_only=True)
    
    # Información de la categoría de la marca
    brand_category_name = serializers.CharField(source='spare_part_brand.id_brands_categories.name', read_only=True)
    brand_category_id = serializers.IntegerField(source='spare_part_brand.id_brands_categories.id_brands_categories', read_only=True)
    
    # No se calcula total; solo se muestra el precio por parte

    class Meta:
        model = MaintenanceSpareParts
        fields = [
            'id_maintenance_spare_parts',
            'name',
            'spare_parts_cost',
            'brand_id',
            'brand_name',
            'brand_description',
            'brand_category_id',
            'brand_category_name',
            'registration_date',
            'modification_date'
        ]
