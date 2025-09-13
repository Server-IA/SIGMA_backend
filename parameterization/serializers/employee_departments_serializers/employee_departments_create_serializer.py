# serializers.py
from rest_framework import serializers
from django.utils import timezone
from parameterization.models import EmployeeDepartment, EmployeeCharge, Statues
from users.models.user import User


class EmployeeDepartmentCreateSerializer(serializers.ModelSerializer):
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    charges = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = EmployeeDepartment
        fields = [
            'name',
            'description',
            'responsible_user',
            'charges',
        ]
        extra_kwargs = {
            'charges': {'write_only': True, 'required': False}
        }

    def validate_name(self, value):
        instance = getattr(self, "instance", None)
        qs = EmployeeDepartment.objects.filter(name__iexact=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Ya existe un departamento con este nombre.")
        return value

    def validate_charges(self, value):
        """
        Validación: evitar cargos duplicados en la misma petición.
        """
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
                f"Los siguientes cargos están duplicados en la petición: {', '.join(duplicates)}"
            )
        return value

    def create(self, validated_data):
        charges_payload = validated_data.pop('charges', [])
        responsible_user = validated_data.pop('responsible_user')
        validated_data['id_responsible_user'] = responsible_user
        validated_data['creation_date'] = timezone.now()
        validated_data['modification_date'] = timezone.now()

        # estado por defecto = 1
        try:
            default_status = Statues.objects.get(pk=1)
        except Statues.DoesNotExist:
            raise serializers.ValidationError("El estado por defecto con id=1 no existe.")

        validated_data['id_statues'] = default_status

        # Crear departamento
        department = EmployeeDepartment.objects.create(**validated_data)

        # Crear cargos asociados
        if isinstance(charges_payload, list):
            for item in charges_payload:
                name = item.get('name')
                if not name:
                    continue

                # Validar que no exista en este mismo departamento
                if EmployeeCharge.objects.filter(
                    id_employee_department=department,
                    name__iexact=name
                ).exists():
                    raise serializers.ValidationError(
                        f"Ya existe un cargo con el nombre '{name}' en este departamento."
                    )

                EmployeeCharge.objects.create(
                    name=name,
                    description=item.get('description', ''),
                    id_employee_department=department,
                    id_statues=default_status,
                    id_responsible_user=responsible_user,
                    creation_date=timezone.now(),
                    modification_date=timezone.now()
                )

        return department

    def update(self, instance, validated_data):
        responsible_user = validated_data.pop('responsible_user', None)
        if responsible_user:
            instance.id_responsible_user = responsible_user

        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.modification_date = timezone.now()
        instance.save()
        return instance