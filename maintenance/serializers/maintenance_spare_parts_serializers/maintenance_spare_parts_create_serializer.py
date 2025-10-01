from rest_framework import serializers
from maintenance.models import MaintenanceSpareParts
from parameterization.models import Brands, BrandsCategory


class MaintenanceSparePartsCreateSerializer(serializers.ModelSerializer):
    """
    Serializador para crear repuestos de mantenimiento.
    Valida que la marca pertenezca a la categoría 4 (marcas de repuestos).
    """
    
    def validate_spare_part_brand(self, value):
        """
        Validar que la marca pertenezca a la categoría con id = 2 (marcas de repuestos).
        """
        if not value:
            raise serializers.ValidationError("La marca es obligatoria.")
        
        if getattr(value.id_brands_categories, "id_brands_categories", None) != 2:
            try:
                expected_category = BrandsCategory.objects.get(id_brands_categories=2)
                raise serializers.ValidationError(
                    f"La marca debe pertenecer a la categoría '{expected_category.name}' (categoría 2)."
                )
            except BrandsCategory.DoesNotExist:
                raise serializers.ValidationError(
                    "La categoría de marcas requerida (id=2) no existe en la parametrización."
                )
        return value
    
    def validate(self, data):
        """
        Validaciones adicionales del serializer.
        """
        # Validar que el precio por parte sea positivo
        if data.get('spare_parts_cost', 0) <= 0:
            raise serializers.ValidationError({
                'spare_parts_cost': 'El precio por parte debe ser mayor a 0.'
            })
        return data

    class Meta:
        model = MaintenanceSpareParts
        fields = [
            'spare_part_brand',
            'name',
            'spare_parts_cost'
        ]
