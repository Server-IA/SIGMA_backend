from rest_framework import serializers
from parameterization.models import Statues

class StatuesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Statues
        fields = [
            'id_statues',
            'name',
            'description',
        ]
