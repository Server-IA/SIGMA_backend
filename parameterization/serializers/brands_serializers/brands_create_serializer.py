from rest_framework import serializers
from django.utils import timezone
from parameterization.models import Brands, BrandsCategory, Statues
from users.models.user import User


class BrandsCreateSerializer(serializers.ModelSerializer):
    brands_category = serializers.PrimaryKeyRelatedField(
        queryset=BrandsCategory.objects.all(), source='id_brands_categories'
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
            'responsible_user',
        ]

    def validate(self, attrs):
        category = attrs.get('id_brands_categories') or getattr(self.instance, 'id_brands_categories', None)
        name = attrs.get('name') or getattr(self.instance, 'name', None)

        if category and name:
            qs = Brands.objects.filter(id_brands_categories=category, name__iexact=name)
            if self.instance:  # si es update
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    'name': f"Ya existe una marca con el nombre '{name}' en esta categoría."
                })
        return attrs

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()

        try:
            default_status = Statues.objects.get(pk=1)
        except Statues.DoesNotExist:
            raise serializers.ValidationError("El estado por defecto con id=1 no existe.")

        validated_data['id_statues'] = default_status

        return Brands.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
