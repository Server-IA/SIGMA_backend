from rest_framework import serializers
from django.utils import timezone
from parameterization.models.units import Units
from parameterization.models.units_category import UnitsCategory
from parameterization.models import Statues
from users.models.user import User


class UnitsCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    units_category = serializers.PrimaryKeyRelatedField(
        queryset=UnitsCategory.objects.all(), source='id_units_categories'
    )

    class Meta:
        model = Units
        fields = [
            'name',
            'description',
            'units_category',
            'responsible_user',
        ]

    def validate(self, attrs):
        category = attrs.get('id_units_categories') or getattr(self.instance, 'id_units_categories', None)
        name = attrs.get('name') or getattr(self.instance, 'name', None)

        if category and name:
            qs = Units.objects.filter(id_units_categories=category, name__iexact=name)
            if self.instance:  # si es update
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    'name': f"Ya existe una unidad con el nombre '{name}' en esta categoría."
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

        return Units.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance


