from rest_framework import serializers
from parameterization.models import UserVisualParameterization

class UserVisualParameterizationListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='id_user.name', read_only=True)
    visual_parameterization_name = serializers.CharField(source='id_visual_parameterization.name', read_only=True)
    user_visual_parameterization_status_name = serializers.CharField(source='user_visual_parameterization_status.name', read_only=True)
    responsible_user_name = serializers.CharField(source='id_responsible_user.name', read_only=True)
    
    class Meta:
        model = UserVisualParameterization
        fields = [
            'id_user_visual_parameterization',
            'id_user',
            'user_name',
            'id_visual_parameterization',
            'visual_parameterization_name',
            'user_visual_parameterization_status',
            'user_visual_parameterization_status_name',
            'registration_date',
            'modification_date',
            'id_responsible_user',
            'responsible_user_name'
        ]
