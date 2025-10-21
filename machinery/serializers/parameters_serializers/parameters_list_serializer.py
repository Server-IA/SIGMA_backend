from rest_framework import serializers
from machinery.models.parameters import Parameters

class ParametersListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameters
        fields = ['id', 'parameter_name', 'avl_id_parameter', 'description', 'minimum_range', 'maximum_range', 'unit', 'minimun_message', 'maximum_message']
