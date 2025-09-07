from rest_framework import serializers
from parameterization.models import BrandsCategory


class BrandsCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandsCategory
        fields = [
            'id_brands_categories',
            'name',
            'description'
        ]


