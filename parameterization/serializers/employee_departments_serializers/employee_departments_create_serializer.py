# serializers.py
from rest_framework import serializers
from parameterization.models import EmployeeDepartment, Statues
from users.models.user import User
from django.utils import timezone

class EmployeeDepartmentCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        write_only=True
    )

    class Meta:
        model = EmployeeDepartment
        fields = [
            'name',
            'description',
            'responsible_user',
        ]

    def validate_name(self, value):
        instance = getattr(self, "instance", None)
        qs = EmployeeDepartment.objects.filter(name__iexact=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Ya existe un departamento con este nombre.")
        return value

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()
        return EmployeeDepartment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user

        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance