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
            # Colores del sistema de diseño
            'primary_color',
            'secondary_color',
            'accent_color',
            'background_color',
            'surface_color',
            'text_color',
            'text_secondary_color',
            'border_color',
            'hover_color',
            'error_color',
            'success_color',
            'warning_color',
            # Tipografía
            'font',
            'title_size',
            'paragraph_size',
            'visual_parameterization_status',
            'visual_parameterization_status_name'
        ]
