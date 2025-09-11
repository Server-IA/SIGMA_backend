from rest_framework import serializers
from parameterization.models import Types

class TypesListSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source='id_statues.name', read_only=True)

    class Meta:
        model = Types
        fields = [
            'id_types',
            'name',
            'description',
            'id_statues',
            'estado',
        ]
