from rest_framework import serializers
from django.utils import timezone
from parameterization.models.units import Units
from parameterization.models.units_category import UnitsCategory
from parameterization.models import Statues
from users.models.user import User


class UnitsCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    units_category = serializers.PrimaryKeyRelatedField(
        queryset=UnitsCategory.objects.all(), source='id_units_categories'
    )
    statues = serializers.PrimaryKeyRelatedField(
        queryset=Statues.objects.all(), source='id_statues'
    )

    class Meta:
        model = Units
        fields = [
            'name',
            'description',
            'units_category',
            'responsible_user',
            'statues',
        ]

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        # Validar que statues sea 1
        statues = validated_data.get('id_statues')
        if not statues or statues.pk != 1:
            raise serializers.ValidationError({
                'statues': 'Solo se permite crear unidades con estatus 1.'
            })
        return Units.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            validated_data['id_responsible_user'] = responsible_user
        # Permitir cambio de statues en actualizaciones
        validated_data['modification_date'] = timezone.now()
        return super().update(instance, validated_data)


