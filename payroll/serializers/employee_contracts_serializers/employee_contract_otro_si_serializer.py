from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from parameterization.models import EmployeeCharge, Statues
from payroll.models import Employee, EmployeeContract, EmployeeNews
from payroll.serializers.employee_contracts_serializers.employee_with_contract_serializer import (
    EmployeeContractCreateSerializer,
)
from users.models import User


class EmployeeContractOtroSiSerializer(serializers.Serializer):
    """
    Serializer para generar un "otro si" (secundary_petition) de un contrato.
    
    Finaliza el contrato actual y crea uno nuevo con secundary_petition=True.
    El start_date se toma del último contrato del empleado.
    """
    observation = serializers.CharField(allow_blank=False, required=True)
    id_employee_charge = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeCharge.objects.all()
    )
    contract = serializers.ListField(child=serializers.DictField(), write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contract_serializer = None
        self._last_contract_start_date = None

    def validate(self, attrs):
        employee = self.context.get("employee")
        if not employee:
            raise serializers.ValidationError("No se proporcionó el empleado.")
        
        # Obtener el último contrato del empleado
        last_contract = (
            EmployeeContract.objects.filter(id_employee=employee)
            .order_by("-creation_date")
            .first()
        )
        
        if not last_contract:
            raise serializers.ValidationError(
                "El empleado no tiene contratos registrados para generar un otro si."
            )
        
        # Validar que el último contrato NO esté finalizado
        if last_contract.contract_status_id == 29:
            raise serializers.ValidationError(
                "No se puede generar un otro si porque el último contrato del empleado está finalizado."
            )
        
        # Guardar el start_date del último contrato
        self._last_contract_start_date = last_contract.start_date
        
        contracts_payload = self.initial_data.get("contract")
        if not isinstance(contracts_payload, list) or not contracts_payload:
            raise serializers.ValidationError(
                {"contract": "Debe proporcionar una lista con la información del contrato."}
            )
        if len(contracts_payload) != 1:
            raise serializers.ValidationError(
                {"contract": "Solo se admite la creación de un contrato por solicitud."}
            )

        # Agregar el start_date del último contrato al payload
        contract_data = contracts_payload[0].copy()
        contract_data["start_date"] = self._last_contract_start_date

        # Validar el contrato usando el serializer existente
        contract_serializer = EmployeeContractCreateSerializer(
            data=contract_data,
            context={"request": self.context.get("request")},
        )
        contract_serializer.is_valid(raise_exception=True)
        self._contract_serializer = contract_serializer
        return attrs

    def _get_responsible_user(self):
        """Obtiene el usuario responsable desde la request."""
        request = self.context.get("request")
        if request and hasattr(request, "user") and getattr(request.user, "id", None):
            try:
                return User.objects.get(pk=request.user.id)
            except User.DoesNotExist:
                pass
        raise serializers.ValidationError(
            {"id_responsible_user": "No se pudo determinar el usuario autenticado."}
        )

    def _get_finished_contract_status(self):
        """Obtiene el estado 29 (Finalizado) para contratos."""
        try:
            return Statues.objects.get(pk=29)
        except Statues.DoesNotExist:
            raise serializers.ValidationError(
                {"contract_status": "No se encontró el estado 29 (Finalizado) para contratos."}
            )

    def _generate_otro_si_contract_code(self, employee):
        """
        Genera el código del "otro si" incrementando el segundo consecutivo (versión).
        
        Lógica:
        - Busca el último contrato del empleado
        - Extrae la base (CON-YYYY-NNNN) y la versión actual (VV)
        - Busca la siguiente versión disponible para esa base
        - Ejemplo: CON-2025-0004-00 → CON-2025-0004-01
        - Ejemplo: CON-2025-0004-01 → CON-2025-0004-02
        - Incluso con cambio de año: CON-2026-0004-02 → CON-2026-0004-03
        """
        # Obtener el último contrato del empleado
        last_contract = (
            EmployeeContract.objects.filter(id_employee=employee)
            .order_by("-creation_date")
            .first()
        )
        
        if not last_contract:
            raise serializers.ValidationError(
                "El empleado no tiene contratos registrados para generar un otro si."
            )
        
        # Parsear el código del último contrato
        # Formato esperado: CON-YYYY-NNNN-VV
        contract_code = last_contract.contract_code
        parts = contract_code.split("-")
        
        try:
            # Extraer la base (CON-YYYY-NNNN)
            base_code = "-".join(parts[:3])  # CON-YYYY-NNNN
            current_version = int(parts[3]) if len(parts) >= 4 else 0
        except (IndexError, ValueError):
            raise serializers.ValidationError(
                f"El formato del código de contrato '{contract_code}' no es válido."
            )
        
        # Buscar la siguiente versión disponible
        # Buscar todos los contratos con la misma base
        existing_versions = EmployeeContract.objects.filter(
            contract_code__startswith=f"{base_code}-"
        ).values_list("contract_code", flat=True)
        
        # Extraer los números de versión existentes
        used_versions = set()
        for code in existing_versions:
            code_parts = code.split("-")
            if len(code_parts) >= 4:
                try:
                    version = int(code_parts[3])
                    used_versions.add(version)
                except ValueError:
                    pass
        
        # Encontrar la siguiente versión libre
        next_version = current_version + 1
        while next_version in used_versions:
            next_version += 1
        
        return f"{base_code}-{next_version:02d}"

    @transaction.atomic
    def create(self, validated_data):
        """
        Crea un "otro si" para el empleado y finaliza el contrato anterior.
        """
        if not self._contract_serializer:
            raise serializers.ValidationError(
                "La información del contrato no fue validada correctamente."
            )

        observation = validated_data["observation"]
        employee_charge = validated_data["id_employee_charge"]
        employee = self.context.get("employee")
        
        if not employee:
            raise serializers.ValidationError("No se proporcionó el empleado.")
        
        responsible_user = self._get_responsible_user()
        finished_status = self._get_finished_contract_status()
        
        # 1. Obtener y finalizar el último contrato del empleado
        last_contract = (
            EmployeeContract.objects.filter(id_employee=employee)
            .order_by("-creation_date")
            .first()
        )
        
        if not last_contract:
            raise serializers.ValidationError(
                "El empleado no tiene contratos registrados para generar un otro si."
            )
        
        # Verificar nuevamente que el último contrato no esté finalizado
        if last_contract.contract_status_id == 29:
            raise serializers.ValidationError(
                "No se puede generar un otro si porque el último contrato del empleado está finalizado."
            )
        
        # Finalizar el contrato actual
        last_contract.contract_status = finished_status
        last_contract.save(update_fields=["contract_status"])
        
        # 2. Generar el código del nuevo contrato (otro si)
        new_contract_code = self._generate_otro_si_contract_code(employee)
        
        # 3. Crear el nuevo contrato con secundary_petition=True
        # Modificar el serializer para usar el código generado
        self._contract_serializer.generate_contract_code = lambda: new_contract_code
        
        # Agregar secundary_petition=True al validated_data del serializer interno
        # Necesitamos modificar el método create del serializer para que acepte este parámetro
        new_contract = self._contract_serializer.save(
            employee=employee,
            employee_charge=employee_charge,
            responsible_user=responsible_user,
        )
        
        # Actualizar el campo secundary_petition manualmente después de la creación
        new_contract.secundary_petition = True
        new_contract.save(update_fields=["secundary_petition"])
        
        # 4. Crear la novedad en EmployeeNews
        EmployeeNews.objects.create(
            id_employee=employee,
            observation=observation,
            news_type="GENERAR_OTRO_SI",
            id_responsible_user=responsible_user,
        )
        
        return {
            "employee_id": employee.id_employee,
            "old_contract_code": last_contract.contract_code,
            "new_contract_code": new_contract.contract_code,
            "secundary_petition": True,
        }
