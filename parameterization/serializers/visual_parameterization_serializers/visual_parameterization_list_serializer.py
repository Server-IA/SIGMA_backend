from rest_framework import serializers
from parameterization.models import VisualParameterization

class VisualParameterizationListSerializer(serializers.ModelSerializer):
    visual_parameterization_status_name = serializers.CharField(source='visual_parameterization_status.name', read_only=True)
    
    class Meta:
        model = VisualParameterization
        fields = [
            'id_visual_parameterization',
            'name',
            'description',
            'background_color',
            'text_color',
            'font',
            'font_size',
            'border_thickness',
            'border_color',
            'visual_parameterization_status',
            'visual_parameterization_status_name'
        ]
