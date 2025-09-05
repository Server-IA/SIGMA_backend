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

    def create(self, validated_data):
        responsible_user = validated_data.pop('responsible_user')

        validated_data['id_responsible_user'] = responsible_user

        # Asigna estado por defecto = 1
        statues = Statues.objects.get(pk=1)
        validated_data['id_statues'] = statues

        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()

        return EmployeeDepartment.objects.create(**validated_data)
