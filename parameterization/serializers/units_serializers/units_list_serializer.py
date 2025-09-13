from rest_framework import serializers
from parameterization.models.units import Units


class UnitsListSerializer(serializers.ModelSerializer):
    statues_name = serializers.CharField(source='id_statues.name', read_only=True)
    units_category_name = serializers.CharField(source='id_units_categories.name', read_only=True)
    unit_type_name = serializers.CharField(source='id_types.name', read_only=True)

    class Meta:
        model = Units
        fields = [
            'id_units',
            'name',
            'symbol',
            'units_category_name',
            'unit_type_name',
            'id_statues',
            'statues_name',
        ]


