from rest_framework import serializers
from parameterization.models.units_category import UnitsCategory


class UnitsCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitsCategory
        fields = [
            'id_units_categories',
            'name',
            'description',
        ]


