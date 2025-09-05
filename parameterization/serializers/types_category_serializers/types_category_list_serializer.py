from rest_framework import serializers
from parameterization.models import TypesCategory

class TypesCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypesCategory
        fields = [
            'id_types_categories',
            'name',
            'description'
        ]
