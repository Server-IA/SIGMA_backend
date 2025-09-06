from rest_framework import serializers
from parameterization.models import Models


class ModelsListSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source='id_brand.name', read_only=True)
    estado = serializers.CharField(source='id_statues.name', read_only=True)

    class Meta:
        model = Models
        fields = [
            'id_model',
            'name',
            'description',
            'brand_name',
            'estado',
        ]


