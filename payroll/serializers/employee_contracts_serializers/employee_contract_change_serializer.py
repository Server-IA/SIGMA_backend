from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from parameterization.models import EmployeeCharge, Statues
from payroll.models import Employee, EmployeeContract, EmployeeNews
from payroll.serializers.employee_contracts_serializers.employee_with_contract_serializer import (
    EmployeeContractCreateSerializer,
)
from users.models import User


class EmployeeContractChangeSerializer(serializers.Serializer):
    """
    Serializer para cambiar el contrato de un empleado.
    
    Finaliza el contrato actual y crea uno nuevo con las mismas validaciones
    que la creación de contratos.
    """
    observation = serializers.CharField(allow_blank=False, required=True)
    id_employee_charge = serializers.PrimaryKeyRelatedField(
        queryset=EmployeeCharge.objects.all()
    )
    contract = serializers.ListField(child=serializers.DictField(), write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contract_serializer = None

    def validate(self, attrs):
        contracts_payload = self.initial_data.get("contract")
        if not isinstance(contracts_payload, list) or not contracts_payload:
            raise serializers.ValidationError(
                {"contract": "Debe proporcionar una lista con la información del contrato."}
            )
        if len(contracts_payload) != 1:
            raise serializers.ValidationError(
                {"contract": "Solo se admite la creación de un contrato por solicitud."}
            )

        # Validar el contrato usando el serializer existente
        contract_serializer = EmployeeContractCreateSerializer(
            data=contracts_payload[0],
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

    def _get_active_contract_status(self):
        """Obtiene el estado 28 (Activo) para contratos."""
        try:
            return Statues.objects.get(pk=28)
        except Statues.DoesNotExist:
            raise serializers.ValidationError(
                {"contract_status": "No se encontró el estado 28 (Activo) para contratos."}
            )

    def _generate_next_contract_code(self, employee):
        """
        Genera el código del siguiente contrato basado en el último contrato GLOBAL del sistema.
        
        Lógica:
        - Busca el último contrato del año actual en toda la base de datos
        - Si existe: incrementa el consecutivo (CON-2025-0004-00 → CON-2025-0005-00)
        - Si no existe o el año cambió: reinicia el consecutivo (CON-2026-0001-00)
        """
        current_year = timezone.now().year
        prefix = f"CON-{current_year}-"
        
        # Buscar el último contrato GLOBAL del año actual
        last_global_contract = (
            EmployeeContract.objects.filter(contract_code__startswith=prefix)
            .order_by("-contract_code")
            .first()
        )
        
        if not last_global_contract:
            # No hay contratos del año actual, empezar desde 0001
            return f"CON-{current_year}-0001-00"
        
        # Parsear el código del último contrato global
        # Formato esperado: CON-YYYY-NNNN-VV
        parts = last_global_contract.contract_code.split("-")
        
        try:
            last_sequence = int(parts[2])
            # Incrementar el consecutivo
            new_sequence = last_sequence + 1
            last_year = int(parts[1])
        except (IndexError, ValueError):
            last_year = current_year - 1  # Forzar reinicio si no se puede parsear
        
        # Determinar si reiniciamos o continuamos el consecutivo
        if last_year == current_year:
            # Mismo año: buscar el último contrato global y continuar
            prefix = f"CON-{current_year}-"
            last_global_contract = (
                EmployeeContract.objects.filter(contract_code__startswith=prefix)
                .order_by("-contract_code")
                .first()
            )
            if last_global_contract:
                parts = last_global_contract.contract_code.split("-")
                try:
                    sequence = int(parts[2]) + 1
                except (IndexError, ValueError):
                    sequence = 1
            else:
                sequence = 1
        else:
            # Año diferente: buscar el último contrato global del año actual
            prefix = f"CON-{current_year}-"
            last_global_contract = (
                EmployeeContract.objects.filter(contract_code__startswith=prefix)
                .order_by("-contract_code")
                .first()
            )
            if last_global_contract:
                # Ya hay contratos este año, continuar desde ahí
                parts = last_global_contract.contract_code.split("-")
                try:
                    sequence = int(parts[2]) + 1
                except (IndexError, ValueError):
                    sequence = 1
            else:
                # Primer contrato del nuevo año
                sequence = 1
        
        return f"CON-{current_year}-{sequence:04d}-00"

    @transaction.atomic
    def create(self, validated_data):
        """
        Crea un nuevo contrato para el empleado y finaliza el anterior.
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
        
        # 1. Finalizar el último contrato del empleado
        last_contract = (
            EmployeeContract.objects.filter(id_employee=employee)
            .order_by("-creation_date")
            .first()
        )
        
        if not last_contract:
            raise serializers.ValidationError(
                "El empleado no tiene contratos registrados para cambiar."
            )
        
        # Finalizar el contrato actual si no está ya finalizado
        if last_contract.contract_status_id != 29:  # Solo actualizar si no está ya finalizado
            last_contract.contract_status = finished_status
            last_contract.save(update_fields=["contract_status"])
        
        # 2. Generar el código del nuevo contrato
        new_contract_code = self._generate_next_contract_code(employee)
        
        # 3. Crear el nuevo contrato
        # Modificar el serializer para usar el código generado
        self._contract_serializer.generate_contract_code = lambda: new_contract_code
        
        new_contract = self._contract_serializer.save(
            employee=employee,
            employee_charge=employee_charge,
            responsible_user=responsible_user,
        )
        
        # 4. Crear la novedad en EmployeeNews
        EmployeeNews.objects.create(
            id_employee=employee,
            observation=observation,
            news_type="CAMBIO_CONTRATO",
            id_responsible_user=responsible_user,
        )
        
        return {
            "employee_id": employee.id_employee,
            "old_contract_code": last_contract.contract_code,
            "new_contract_code": new_contract.contract_code,
        }
