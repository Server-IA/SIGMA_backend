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
            'name': {'required': True},
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
        Validaciones:
        - evitar cargos duplicados en la misma petición.
        - asegurar que cada cargo incluya contract_prefix y sea único globalmente.
        - validar que contract_prefix solo contenga letras
        """
        if not isinstance(value, list):
            return value

        seen_names = set()
        duplicate_names = []
        seen_prefixes = set()
        duplicate_prefixes = []
        missing_prefix = []
        invalid_prefix = []
        invalid_chars = []
        existing_prefixes = []

        for item in value:
            name = (item.get("name") or "").strip()
            contract_prefix = (item.get("contract_prefix") or "").strip()

            if not contract_prefix:
                missing_prefix.append(name or "Sin nombre")

            if name:
                lname = name.lower()
                if lname in seen_names:
                    duplicate_names.append(name)
                else:
                    seen_names.add(lname)

            if contract_prefix:
                # Check for whitespace
                if any(ch.isspace() for ch in contract_prefix):
                    invalid_prefix.append(contract_prefix)
                    continue
                    
                # Check for non-letter characters
                if not contract_prefix.isalpha():
                    invalid_chars.append(contract_prefix)
                    continue
                    
                lprefix = contract_prefix.lower()
                if lprefix in seen_prefixes:
                    duplicate_prefixes.append(contract_prefix)
                else:
                    seen_prefixes.add(lprefix)
                    if EmployeeCharge.objects.filter(contract_prefix__iexact=contract_prefix).exists():
                        existing_prefixes.append(contract_prefix)

        errors = []
        if missing_prefix:
            errors.append(
                f"Los siguientes cargos no tienen prefijo de contrato: {', '.join(missing_prefix)}"
            )
        if duplicate_names:
            errors.append(
                f"Los siguientes cargos están duplicados en la petición: {', '.join(duplicate_names)}"
            )
        if duplicate_prefixes:
            errors.append(
                f"Los siguientes prefijos de contrato están duplicados en la petición: {', '.join(duplicate_prefixes)}"
            )
        if invalid_prefix:
            errors.append(
                f"Los siguientes prefijos de contrato contienen espacios y no son válidos: {', '.join(invalid_prefix)}"
            )
        if invalid_chars:
            errors.append(
                f"Los siguientes prefijos de contrato contienen caracteres inválidos (solo se permiten letras): {', '.join(invalid_chars)}"
            )
        if existing_prefixes:
            errors.append(
                f"Ya existe un cargo registrado con el prefijo de contrato: {', '.join(existing_prefixes)}"
            )

        if errors:
            raise serializers.ValidationError(" ".join(errors))

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
                contract_prefix = item.get('contract_prefix')
                if not contract_prefix:
                    raise serializers.ValidationError(
                        f"El cargo '{name}' no especifica contract_prefix."
                    )
                contract_prefix = contract_prefix.strip().upper()

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
                    contract_prefix=contract_prefix,
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