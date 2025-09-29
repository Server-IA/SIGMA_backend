from rest_framework import serializers
from parameterization.models import Types, TypesCategory, Statues
from users.models.user import User
from django.utils import timezone


class TypesCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    types_category = serializers.PrimaryKeyRelatedField(
        queryset=TypesCategory.objects.all(),
        source='id_types_categories'
    )

    class Meta:
        model = Types
        fields = [
            'name',
            'description',
            'types_category',
            'responsible_user',
        ]

        extra_kwargs = {
            'name': {'required': True}
        }
    def validate(self, attrs):
        category = attrs.get('id_types_categories') or getattr(self.instance, 'id_types_categories', None)
        name = attrs.get('name') or getattr(self.instance, 'name', None)

        if category and name:
            qs = Types.objects.filter(id_types_categories=category, name__iexact=name)
            if self.instance:  # si es update
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError({
                    'name': f"Ya existe un tipo con el nombre '{name}' en esta categoría."
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

        return Types.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
