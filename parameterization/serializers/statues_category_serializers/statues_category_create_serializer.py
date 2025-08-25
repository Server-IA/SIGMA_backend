from rest_framework import serializers
from parameterization.models import StatuesCategory
from users.models.user import User
from django.utils import timezone

class StatuesCategoryCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = StatuesCategory
        fields = [
            'name',
            'description',
            'responsible_user',
        ]

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return StatuesCategory.objects.create(**validated_data)
