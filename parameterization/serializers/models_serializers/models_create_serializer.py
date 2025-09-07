from rest_framework import serializers
from django.utils import timezone
from parameterization.models import Models, Brands, Statues
from users.models.user import User


class ModelsCreateSerializer(serializers.ModelSerializer):
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brands.objects.all(), source='id_brand'
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

        try:
            default_status = Statues.objects.get(pk=1)
        except Statues.DoesNotExist:
            raise serializers.ValidationError("El estado por defecto con id=1 no existe.")

        validated_data['id_statues'] = default_status

        return Models.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance


