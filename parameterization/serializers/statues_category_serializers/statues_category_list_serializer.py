from rest_framework import serializers
from parameterization.models import StatuesCategory

class StatuesCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatuesCategory
        fields = [
            'id_statues_categories',
            'name',
            'description'
        ]
