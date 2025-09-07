from rest_framework import serializers
from parameterization.models import Brands


class BrandsListSerializer(serializers.ModelSerializer):
    brands_category_name = serializers.CharField(source='id_brands_categories.name', read_only=True)
    estado = serializers.CharField(source='id_statues.name', read_only=True)

    class Meta:
        model = Brands
        fields = [
            'id_brands',
            'name',
            'description',
            'brands_category_name',
            'estado'
        ]


