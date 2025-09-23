from rest_framework import serializers
from parameterization.models import Types

class MaintenanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Types
        fields = ("id_types", "name")