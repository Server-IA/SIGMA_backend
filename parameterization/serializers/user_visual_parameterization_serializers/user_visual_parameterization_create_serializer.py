from rest_framework import serializers
from parameterization.models import UserVisualParameterization
from users.models.user import User
from parameterization.models import VisualParameterization, Statues
from django.utils import timezone
from django.core.exceptions import ValidationError

class UserVisualParameterizationCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='id_user'
    )
    visual_parameterization = serializers.PrimaryKeyRelatedField(
        queryset=VisualParameterization.objects.all(), write_only=True, source='id_visual_parameterization'
    )
    user_visual_parameterization_status = serializers.PrimaryKeyRelatedField(
        queryset=Statues.objects.all(), write_only=True, required=False
    )
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = UserVisualParameterization
        fields = [
            'user',
            'visual_parameterization',
            'user_visual_parameterization_status',
            'responsible_user',
        ]

    def validate(self, data):
        """
        Validación personalizada para asegurar que todos los campos requeridos estén presentes
        """
        required_fields = [
            'id_user', 'id_visual_parameterization', 'responsible_user'
        ]
        
        errors = {}
        
        # Verificar que todos los campos requeridos estén presentes
        for field in required_fields:
            if field not in data:
                errors[field] = f"El campo '{field}' es requerido"
            elif data[field] is None:
                errors[field] = f"El campo '{field}' no puede estar vacío"
        
        # Si el cliente envía un estado distinto de 1 en POST, marcar error
        if 'user_visual_parameterization_status' in data and data['user_visual_parameterization_status'] is not None:
            provided_status = getattr(data['user_visual_parameterization_status'], 'pk', None)
            if provided_status != 1:
                errors['user_visual_parameterization_status'] = "En creación el estado debe ser 1."
        
        if errors:
            raise ValidationError(errors)
        
        return data

    def create(self, validated_data):
        # Forzar estado = 1 en POST
        validated_data['user_visual_parameterization_status'] = Statues.objects.get(pk=1)
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['registration_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return UserVisualParameterization.objects.create(**validated_data)
