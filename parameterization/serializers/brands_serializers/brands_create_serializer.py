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
    models = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
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

    def validate_models(self, value):
        if not isinstance(value, list):
            return value

        seen = set()
        duplicates = []
        for item in value:
            name = item.get("name")
            if not name:
                continue
            lname = name.strip().lower()
            if lname in seen:
                duplicates.append(name)
            else:
                seen.add(lname)
        if duplicates:
            raise serializers.ValidationError(
                f"Los siguientes modelos están duplicados en la petición: {', '.join(duplicates)}"
            )
        return value

    def create(self, validated_data):
        models_payload = validated_data.pop('models', [])
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()

        try:
            default_status = Statues.objects.get(pk=1)
        except Statues.DoesNotExist:
            raise serializers.ValidationError("El estado por defecto con id=1 no existe.")

        validated_data['id_statues'] = default_status

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
                    id_statues=default_status,
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
