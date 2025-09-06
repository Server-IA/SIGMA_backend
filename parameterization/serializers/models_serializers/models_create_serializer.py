from rest_framework import serializers
from django.utils import timezone
from parameterization.models import Models, Brands, Statues
from users.models.user import User


class ModelsCreateSerializer(serializers.ModelSerializer):
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brands.objects.all(), source='id_brand'
    )
    statues = serializers.PrimaryKeyRelatedField(
        queryset=Statues.objects.all(), source='id_statues'
    )
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = Models
        fields = [
            'name',
            'description',
            'brand',
            'statues',
            'responsible_user',
        ]

    def validate_name(self, value):
        # Unicidad por marca
        instance = getattr(self, "instance", None)
        brand = self.initial_data.get('brand') or (
            getattr(instance, 'id_brand_id', None) if instance else None
        )
        if brand is not None:
            qs = Models.objects.filter(name__iexact=value, id_brand_id=brand)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError("Ya existe un modelo con este nombre en esta marca.")
        return value

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return Models.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.id_brand = validated_data.get('id_brand', instance.id_brand)
        instance.modification_date = timezone.now()
        instance.save()
        return instance


