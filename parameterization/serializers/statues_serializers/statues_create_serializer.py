from rest_framework import serializers
from parameterization.models import Statues, StatuesCategory
from users.models.user import User
from django.utils import timezone

class StatuesCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    statues_category = serializers.PrimaryKeyRelatedField(
        queryset=StatuesCategory.objects.all(),
        source='id_statues_categories'
    )

    class Meta:
        model = Statues
        fields = [
            'name',
            'description',
            'statues_category',
            'responsible_user',
        ]

    def validate(self, attrs):
        category = attrs.get('id_statues_categories') or getattr(self.instance, 'id_statues_categories', None)
        name = attrs.get('name') or getattr(self.instance, 'name', None)

        if category and name:
            qs = Statues.objects.filter(id_statues_categories=category, name__iexact=name)
            if self.instance:  # si es update
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    'name': f"Ya existe un estado con el nombre '{name}' en esta categoría."
                })
        return attrs

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return Statues.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
