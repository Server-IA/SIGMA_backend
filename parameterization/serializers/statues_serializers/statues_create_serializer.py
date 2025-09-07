from rest_framework import serializers
from parameterization.models import Statues, StatuesCategory
from users.models.user import User
from django.utils import timezone

class StatuesCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    statues_category = serializers.PrimaryKeyRelatedField(
        queryset=StatuesCategory.objects.all(), source='id_statues_categories'
    )

    class Meta:
        model = Statues
        fields = [
            'name',
            'description',
            'statues_category',
            'responsible_user',
        ]

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return Statues.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
