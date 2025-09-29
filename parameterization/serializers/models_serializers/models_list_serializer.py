from rest_framework import serializers
from parameterization.models import Models


class ModelsListSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source='id_statues.name', read_only=True)

    class Meta:
        model = Models
        fields = [
            'id_model',
            'name',
            'description',
            'id_brand',
            'id_statues',
            'estado',
        ]


