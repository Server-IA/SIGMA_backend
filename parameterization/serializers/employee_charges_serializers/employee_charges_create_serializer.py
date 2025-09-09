from rest_framework import serializers
from parameterization.models import EmployeeCharge, EmployeeDepartment, Statues
from users.models.user import User
from django.utils import timezone


class EmployeeChargeCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeDepartment.objects.all(),
        source='id_employee_department',
        write_only=True
    )

    class Meta:
        model = EmployeeCharge
        fields = [
            'name',
            'description',
            'department',
            'responsible_user',
        ]

    def validate(self, attrs):
        dept = attrs.get('id_employee_department') or getattr(self.instance, 'id_employee_department', None)
        name = attrs.get('name') or getattr(self.instance, 'name', None)

        if dept and name:
            qs = EmployeeCharge.objects.filter(id_employee_department=dept, name__iexact=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'name': f"Ya existe un cargo con el nombre '{name}' en este departamento."
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
            raise serializers.ValidationError({
            })

        validated_data['id_statues'] = default_status

        return EmployeeCharge.objects.create(**validated_data)

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance
