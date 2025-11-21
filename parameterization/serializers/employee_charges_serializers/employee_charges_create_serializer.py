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
            'contract_prefix',
            'description',
            'department',
            'responsible_user',
        ]
        extra_kwargs = {
            'name': {'required': True},
            'contract_prefix': {'required': True}
        }

    def validate(self, attrs):
        dept = attrs.get('id_employee_department') or getattr(self.instance, 'id_employee_department', None)
        name = attrs.get('name') or getattr(self.instance, 'name', None)
        contract_prefix = attrs.get('contract_prefix')

        if contract_prefix is None:
            contract_prefix = getattr(self.instance, 'contract_prefix', None)
        else:
            contract_prefix = contract_prefix.strip()

        if not contract_prefix:
            raise serializers.ValidationError({
                'contract_prefix': "El prefijo de contrato es obligatorio."
            })

        if any(ch.isspace() for ch in contract_prefix):
            raise serializers.ValidationError({
                'contract_prefix': "El prefijo de contrato no puede contener espacios."
            })

        normalized_prefix = contract_prefix.upper()
        prefix_qs = EmployeeCharge.objects.filter(contract_prefix__iexact=normalized_prefix)
        if self.instance:
            prefix_qs = prefix_qs.exclude(pk=self.instance.pk)
        if prefix_qs.exists():
            raise serializers.ValidationError({
                'contract_prefix': "Ya existe un cargo con este prefijo de contrato."
            })
        attrs['contract_prefix'] = normalized_prefix

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

        contract_prefix = validated_data.get('contract_prefix')
        if contract_prefix:
            validated_data['contract_prefix'] = contract_prefix.strip().upper()

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
        if 'contract_prefix' in validated_data:
            instance.contract_prefix = validated_data['contract_prefix']
        instance.modification_date = timezone.now()
        instance.save()
        return instance
