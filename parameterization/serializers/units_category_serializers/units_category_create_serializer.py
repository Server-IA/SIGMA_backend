from rest_framework import serializers
from django.utils import timezone
from parameterization.models.units_category import UnitsCategory
from users.models.user import User


class UnitsCategoryCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = UnitsCategory
        fields = [
            'name',
            'description',
            'responsible_user',
        ]

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return UnitsCategory.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            validated_data['id_responsible_user'] = responsible_user
        validated_data['modification_date'] = timezone.now()
        return super().update(instance, validated_data)


