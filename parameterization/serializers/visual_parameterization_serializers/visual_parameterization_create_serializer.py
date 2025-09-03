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
            'background_color',
            'text_color',
            'font',
            'font_size',
            'border_thickness',
            'border_color',
            'visual_parameterization_status',
            'responsible_user',
        ]

    def validate(self, data):
        """
        Validación personalizada para asegurar que todos los campos requeridos estén presentes y no vacíos
        y que el contraste de colores cumpla con WCAG AA.
        """
        required_fields = [
            'name', 'description', 'background_color', 'text_color', 
            'font', 'font_size', 'border_thickness', 'border_color',
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
        text_fields = ['name', 'description', 'background_color', 'text_color', 'font', 'font_size', 'border_thickness', 'border_color']
        for field in text_fields:
            if field in data and data[field]:
                if len(str(data[field]).strip()) == 0:
                    errors[field] = f"El campo '{field}' no puede estar vacío"
                elif len(str(data[field]).strip()) > 255:
                    errors[field] = f"El campo '{field}' no puede tener más de 255 caracteres"
        
        # Validación de contraste WCAG AA entre fondo y texto
        background_color = data.get('background_color')
        text_color = data.get('text_color')
        if background_color and text_color:
            validator = ContrastValidator()
            contrast = validator.validate_contrast(background_color, text_color, level='AA', text_size='normal')
            if not contrast.get('valid', False):
                errors['contrast'] = (
                    f"El contraste entre el color de fondo ({background_color}) y el texto ({text_color}) "
                    f"no cumple con WCAG AA. Ratio actual: {contrast.get('contrast_ratio')}:1, "
                    f"mínimo requerido: {contrast.get('threshold')}:1."
                )
        
        # Opcional: validar contraste del borde con el fondo (típicamente texto grande)
        border_color = data.get('border_color')
        if background_color and border_color:
            validator = ContrastValidator()
            border_contrast = validator.validate_contrast(background_color, border_color, level='AA', text_size='large')
            if not border_contrast.get('valid', False):
                errors['border_contrast'] = (
                    f"El contraste entre el color de fondo ({background_color}) y el borde ({border_color}) "
                    f"es insuficiente. Ratio actual: {border_contrast.get('contrast_ratio')}:1, "
                    f"mínimo requerido: {border_contrast.get('threshold')}:1."
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
