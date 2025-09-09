from rest_framework import serializers
from parameterization.models import VisualParameterization
from users.models.user import User
from parameterization.models import Statues
from django.utils import timezone
from django.core.exceptions import ValidationError
from parameterization.services.contrast_service import ContrastValidator

class VisualParameterizationCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    visual_parameterization_status = serializers.PrimaryKeyRelatedField(
        queryset=Statues.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = VisualParameterization
        fields = [
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
            'responsible_user',
        ]

    def validate(self, data):
        """
        Validación personalizada para asegurar que todos los campos requeridos estén presentes y no vacíos
        y que el contraste de colores cumpla con WCAG AA.
        """
        required_fields = [
            'name', 'description', 'primary_color', 'secondary_color', 'accent_color',
            'background_color', 'surface_color', 'text_color', 'text_secondary_color',
            'border_color', 'hover_color', 'error_color', 'success_color', 'warning_color',
            'font', 'title_size', 'paragraph_size',
            # 'visual_parameterization_status' ya no es requerido en POST
            'responsible_user'
        ]
        
        errors = {}
        
        # Verificar que todos los campos requeridos estén presentes
        for field in required_fields:
            if field not in data:
                errors[field] = f"El campo '{field}' es requerido"
            elif data[field] is None or str(data[field]).strip() == '':
                errors[field] = f"El campo '{field}' no puede estar vacío"
        
        # Si el cliente envía un estado distinto de 1 en POST, marcar error
        if 'visual_parameterization_status' in data and data['visual_parameterization_status'] is not None:
            provided_status = getattr(data['visual_parameterization_status'], 'pk', None)
            if provided_status != 1:
                errors['visual_parameterization_status'] = "En creación el estado debe ser 1."
        
        # Validaciones específicas para campos de texto
        text_fields = [
            'name', 'description', 'primary_color', 'secondary_color', 'accent_color',
            'background_color', 'surface_color', 'text_color', 'text_secondary_color',
            'border_color', 'hover_color', 'error_color', 'success_color', 'warning_color',
            'font'
        ]
        for field in text_fields:
            if field in data and data[field]:
                if len(str(data[field]).strip()) == 0:
                    errors[field] = f"El campo '{field}' no puede estar vacío"
                elif len(str(data[field]).strip()) > 255:
                    errors[field] = f"El campo '{field}' no puede tener más de 255 caracteres"
        
        # Validaciones específicas para tamaños tipográficos
        typography_sizes = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl']
        if 'title_size' in data and data['title_size']:
            if data['title_size'] not in typography_sizes:
                errors['title_size'] = f"El tamaño de título debe ser uno de: {', '.join(typography_sizes)}"
        if 'paragraph_size' in data and data['paragraph_size']:
            if data['paragraph_size'] not in typography_sizes:
                errors['paragraph_size'] = f"El tamaño de párrafo debe ser uno de: {', '.join(typography_sizes)}"
        
        # Validaciones de contraste WCAG AA para todos los colores
        validator = ContrastValidator()
        background_color = data.get('background_color')
        
        # Validar contraste de colores principales con el fondo
        color_contrasts = [
            ('primary_color', 'primary_color', background_color, 'normal'),
            ('secondary_color', 'secondary_color', background_color, 'normal'),
            ('accent_color', 'accent_color', background_color, 'normal'),
            ('text_color', 'text_color', background_color, 'normal'),
            ('text_secondary_color', 'text_secondary_color', background_color, 'normal'),
            ('error_color', 'error_color', background_color, 'normal'),
            ('success_color', 'success_color', background_color, 'normal'),
            ('warning_color', 'warning_color', background_color, 'normal'),
            ('border_color', 'border_color', background_color, 'large'),
        ]
        
        for field_name, color1_field, color2_field, text_size in color_contrasts:
            color1 = data.get(color1_field)
            color2 = data.get(color2_field)
            if color1 and color2:
                contrast = validator.validate_contrast(color1, color2, level='AA', text_size=text_size)
                if not contrast.get('valid', False):
                    errors[f'{field_name}_contrast'] = (
                        f"El contraste entre {color1_field} ({color1}) y {color2_field} ({color2}) "
                        f"no cumple con WCAG AA. Ratio actual: {contrast.get('contrast_ratio')}:1, "
                        f"mínimo requerido: {contrast.get('threshold')}:1."
                    )
        
        # Validar contraste de surface_color con text_color
        surface_color = data.get('surface_color')
        text_color = data.get('text_color')
        if surface_color and text_color:
            contrast = validator.validate_contrast(surface_color, text_color, level='AA', text_size='normal')
            if not contrast.get('valid', False):
                errors['surface_text_contrast'] = (
                    f"El contraste entre surface_color ({surface_color}) y text_color ({text_color}) "
                    f"no cumple con WCAG AA. Ratio actual: {contrast.get('contrast_ratio')}:1, "
                    f"mínimo requerido: {contrast.get('threshold')}:1."
                )
        
        # Validar contraste de hover_color con text_color
        hover_color = data.get('hover_color')
        if hover_color and text_color:
            contrast = validator.validate_contrast(hover_color, text_color, level='AA', text_size='normal')
            if not contrast.get('valid', False):
                errors['hover_text_contrast'] = (
                    f"El contraste entre hover_color ({hover_color}) y text_color ({text_color}) "
                    f"no cumple con WCAG AA. Ratio actual: {contrast.get('contrast_ratio')}:1, "
                    f"mínimo requerido: {contrast.get('threshold')}:1."
                )
        
        if errors:
            raise ValidationError(errors)
        
        return data

    def create(self, validated_data):
        # Forzar estado = 1 en POST
        validated_data['visual_parameterization_status'] = Statues.objects.get(pk=1)
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return VisualParameterization.objects.create(**validated_data)
