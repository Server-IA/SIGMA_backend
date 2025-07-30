from rest_framework import serializers
from users.models.role import Role
from parameterization.models import Statues
from users.models.user import User
from django.utils import timezone

class RoleCreateSerializer(serializers.ModelSerializer):
    rol_status = serializers.PrimaryKeyRelatedField(
        queryset=Statues.objects.all(),
        required=False
    )
    id_responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Role
        fields = ['name', 'rol_status', 'id_responsible_user']

    def create(self, validated_data):
        from parameterization.models import StatuesCategory, Statues

        if 'rol_status' not in validated_data:
            try:
                category = StatuesCategory.objects.get(name='GENERAL_STATUS')
                estado_activo = Statues.objects.get(name='ACTIVO', id_statues_categories=category)
                validated_data['rol_status'] = estado_activo
            except StatuesCategory.DoesNotExist:
                raise serializers.ValidationError({"rol_status": "Categoría 'GENERAL_STATUS' no encontrada."})
            except Statues.DoesNotExist:
                raise serializers.ValidationError({"rol_status": "Estado 'ACTIVO' para roles no encontrado."})

        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return Role.objects.create(**validated_data)
