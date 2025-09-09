from rest_framework import serializers
from parameterization.models import VisualParameterization
from users.models.user import User
from parameterization.models import Statues
from django.utils import timezone
from django.core.exceptions import ValidationError
from parameterization.services.contrast_service import ContrastValidator

class VisualParameterizationUpdateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=False
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
        extra_kwargs = {field: { 'required': False } for field in fields}

    def validate(self, data):
        """
        Para PUT (partial=False): exigir todos los campos y no vacíos.
        Para PATCH (partial=True): validar solo los enviados; si se envía uno de los colores,
        combinar con el valor actual de la instancia para validar contraste.
        """
        errors = {}
        is_partial = getattr(self, 'partial', False)

        # Campos a validar como texto
        text_fields = [
            'name', 'description', 'primary_color', 'secondary_color', 'accent_color',
            'background_color', 'surface_color', 'text_color', 'text_secondary_color',
            'border_color', 'hover_color', 'error_color', 'success_color', 'warning_color',
            'font'
        ]

        if not is_partial:
            # PUT: exigir todos los campos
            required_fields = [
                'name', 'description', 'primary_color', 'secondary_color', 'accent_color',
                'background_color', 'surface_color', 'text_color', 'text_secondary_color',
                'border_color', 'hover_color', 'error_color', 'success_color', 'warning_color',
                'font', 'title_size', 'paragraph_size',
                'visual_parameterization_status', 'responsible_user'
            ]
            for field in required_fields:
                if field not in data:
                    errors[field] = f"El campo '{field}' es requerido"
                elif data[field] is None or str(data[field]).strip() == '':
                    errors[field] = f"El campo '{field}' no puede estar vacío"
        else:
            # PATCH: validar no-vacío para campos presentes
            for field, value in data.items():
                if value is None or (isinstance(value, str) and str(value).strip() == ''):
                    errors[field] = f"El campo '{field}' no puede estar vacío"

        # Validación de longitud en campos de texto presentes
        for field in text_fields:
            if field in data and data[field]:
                value = str(data[field]).strip()
                if len(value) == 0:
                    errors[field] = f"El campo '{field}' no puede estar vacío"
                elif len(value) > 255:
                    errors[field] = f"El campo '{field}' no puede tener más de 255 caracteres"
        
        # Validaciones específicas para tamaños tipográficos
        typography_sizes = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl']
        if 'title_size' in data and data['title_size']:
            if data['title_size'] not in typography_sizes:
                errors['title_size'] = f"El tamaño de título debe ser uno de: {', '.join(typography_sizes)}"
        if 'paragraph_size' in data and data['paragraph_size']:
            if data['paragraph_size'] not in typography_sizes:
                errors['paragraph_size'] = f"El tamaño de párrafo debe ser uno de: {', '.join(typography_sizes)}"

        # Validación de contraste
        validator = ContrastValidator()
        background_color = data.get('background_color', getattr(self.instance, 'background_color', None))
        text_color = data.get('text_color', getattr(self.instance, 'text_color', None))
        
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
            color1 = data.get(color1_field, getattr(self.instance, color1_field, None))
            color2 = data.get(color2_field, getattr(self.instance, color2_field, None))
            if color1 and color2:
                contrast = validator.validate_contrast(color1, color2, level='AA', text_size=text_size)
                if not contrast.get('valid', False):
                    errors[f'{field_name}_contrast'] = (
                        f"El contraste entre {color1_field} ({color1}) y {color2_field} ({color2}) "
                        f"no cumple con WCAG AA. Ratio actual: {contrast.get('contrast_ratio')}:1, "
                        f"mínimo requerido: {contrast.get('threshold')}:1."
                    )
        
        # Validar contraste de surface_color con text_color
        surface_color = data.get('surface_color', getattr(self.instance, 'surface_color', None))
        if surface_color and text_color:
            contrast = validator.validate_contrast(surface_color, text_color, level='AA', text_size='normal')
            if not contrast.get('valid', False):
                errors['surface_text_contrast'] = (
                    f"El contraste entre surface_color ({surface_color}) y text_color ({text_color}) "
                    f"no cumple con WCAG AA. Ratio actual: {contrast.get('contrast_ratio')}:1, "
                    f"mínimo requerido: {contrast.get('threshold')}:1."
                )
        
        # Validar contraste de hover_color con text_color
        hover_color = data.get('hover_color', getattr(self.instance, 'hover_color', None))
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

    def update(self, instance, validated_data):
        # Mantener creation_date intacto; actualizar modification_date
        if 'responsible_user' in validated_data:
            instance.id_responsible_user = validated_data.pop('responsible_user')
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
