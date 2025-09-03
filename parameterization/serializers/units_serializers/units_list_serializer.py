from rest_framework import serializers
from parameterization.models.units import Units


class UnitsListSerializer(serializers.ModelSerializer):
    statues_name = serializers.CharField(source='id_statues.name', read_only=True)
    units_category_name = serializers.CharField(source='id_units_categories.name', read_only=True)

    class Meta:
        model = Units
        fields = [
            'id_units',
            'name',
            'description',
            'units_category_name',
            'statues_name',
        ]


