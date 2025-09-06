from rest_framework import serializers
from django.utils import timezone
from parameterization.models import Brands, BrandsCategory, Statues
from users.models.user import User


class BrandsCreateSerializer(serializers.ModelSerializer):
    brands_category = serializers.PrimaryKeyRelatedField(
        queryset=BrandsCategory.objects.all(), source='id_brands_categories'
    )
    statues = serializers.PrimaryKeyRelatedField(
        queryset=Statues.objects.all(), source='id_statues'
    )
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = Brands
        fields = [
            'name',
            'description',
            'brands_category',
            'statues',
            'responsible_user',
        ]

    def validate_name(self, value):
        instance = getattr(self, "instance", None)
        qs = Brands.objects.filter(name__iexact=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una marca con este nombre.")
        return value

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return Brands.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.id_brands_categories = validated_data.get('id_brands_categories', instance.id_brands_categories)
        instance.id_statues = validated_data.get('id_statues', instance.id_statues)
        instance.modification_date = timezone.now()
        instance.save()
        return instance


