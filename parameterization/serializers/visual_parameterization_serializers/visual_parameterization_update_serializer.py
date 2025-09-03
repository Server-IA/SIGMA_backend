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
            'background_color',
            'text_color',
            'font',
            'font_size',
            'border_thickness',
            'border_color',
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
        text_fields = ['name', 'description', 'background_color', 'text_color', 'font', 'font_size', 'border_thickness', 'border_color']

        if not is_partial:
            # PUT: exigir todos los campos
            required_fields = [
                'name', 'description', 'background_color', 'text_color',
                'font', 'font_size', 'border_thickness', 'border_color',
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

        # Validación de contraste
        validator = ContrastValidator()
        background_color = data.get('background_color', getattr(self.instance, 'background_color', None))
        text_color = data.get('text_color', getattr(self.instance, 'text_color', None))
        if background_color and text_color:
            contrast = validator.validate_contrast(background_color, text_color, level='AA', text_size='normal')
            if not contrast.get('valid', False):
                errors['contrast'] = (
                    f"El contraste entre el color de fondo ({background_color}) y el texto ({text_color}) "
                    f"no cumple con WCAG AA. Ratio actual: {contrast.get('contrast_ratio')}:1, "
                    f"mínimo requerido: {contrast.get('threshold')}:1."
                )

        # Contraste del borde
        border_color = data.get('border_color', getattr(self.instance, 'border_color', None))
        if background_color and border_color:
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

    def update(self, instance, validated_data):
        # Mantener creation_date intacto; actualizar modification_date
        if 'responsible_user' in validated_data:
            instance.id_responsible_user = validated_data.pop('responsible_user')
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
