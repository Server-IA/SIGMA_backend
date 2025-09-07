from rest_framework import serializers
from django.utils import timezone
from parameterization.models import Brands, BrandsCategory, Statues, Models
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
            'models',
        ]
        extra_kwargs = {
            'models': {'write_only': True, 'required': False}
        }

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
    def validate(self, attrs):
        # Validar unicidad del nombre por categoría
        instance = getattr(self, "instance", None)
        name = attrs.get('name', getattr(instance, 'name', None))
        category_id = None
        if 'id_brands_categories' in attrs:
            category_id = getattr(attrs['id_brands_categories'], 'pk', None)
        else:
            category_id = getattr(instance, 'id_brands_categories_id', None)

        if name and category_id:
            qs = Brands.objects.filter(name__iexact=name, id_brands_categories_id=category_id)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'name': 'Ya existe una marca con este nombre en esta categoría.'
                })
        return attrs

    def create(self, validated_data):
        models_payload = self.initial_data.get('models', [])
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
        brand = Brands.objects.create(**validated_data)

        # Crear modelos asociados si se enviaron
        if isinstance(models_payload, list):
            for item in models_payload:
                name = item.get('name')
                if not name:
                    continue
                Models.objects.create(
                    name=name,
                    description=item.get('description', ''),
                    id_brand=brand,
                    id_statues=Statues.objects.get(pk=item.get('statues', 1)),
                    id_responsible_user=responsible_user,
                    creation_date=timezone.now(),
                    modification_date=timezone.now()
                )
        return brand

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
