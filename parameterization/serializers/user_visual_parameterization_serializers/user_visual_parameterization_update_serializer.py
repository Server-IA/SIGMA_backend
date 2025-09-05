from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError
from parameterization.models import UserVisualParameterization, VisualParameterization, Statues
from users.models.user import User

class UserVisualParameterizationUpdateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='id_user', required=False
    )
    visual_parameterization = serializers.PrimaryKeyRelatedField(
        queryset=VisualParameterization.objects.all(), write_only=True, source='id_visual_parameterization', required=False
    )
    user_visual_parameterization_status = serializers.PrimaryKeyRelatedField(
        queryset=Statues.objects.all(), write_only=True, required=False
    )
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = UserVisualParameterization
        fields = [
            'user',
            'visual_parameterization',
            'user_visual_parameterization_status',
            'responsible_user',
        ]
        extra_kwargs = {field: {'required': False} for field in fields}

    def validate(self, data):
        errors = {}
        is_partial = getattr(self, 'partial', False)

        if not is_partial:
            # PUT: exigir todos los campos
            required_fields = [
                'id_user', 'id_visual_parameterization', 'user_visual_parameterization_status', 'responsible_user'
            ]
            for field in required_fields:
                if field not in data:
                    errors[field] = f"El campo '{field}' es requerido"
                elif data[field] is None:
                    errors[field] = f"El campo '{field}' no puede estar vacío"
        else:
            # PATCH: validar no-vacío para los que vengan
            for field, value in data.items():
                if value is None:
                    errors[field] = f"El campo '{field}' no puede estar vacío"

        if errors:
            raise ValidationError(errors)
        return data

    def update(self, instance, validated_data):
        # Mapear responsible_user y dejar que DRF maneje FKs por PK
        if 'responsible_user' in validated_data:
            instance.id_responsible_user = validated_data.pop('responsible_user')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
