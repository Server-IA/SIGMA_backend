import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from payroll.models import EmployeeContract
from payroll.serializers.employee_contracts_serializers.employee_contract_detail_serializer import (
    EmployeeContractDetailSerializer,
)
from payroll.serializers.employee_contracts_serializers.employee_with_contract_serializer import (
    EmployeeWithContractCreateSerializer,
)

logger = logging.getLogger(__name__)


class EmployeeViewSet(viewsets.ViewSet):
    """Gestiona la creación de empleados junto con su contrato asociado."""

    def check_permission(self, request, required_permission_id: int) -> bool:
        payload = getattr(request, "auth", None) or {}
        user_roles = payload.get("rol") or payload.get("roles") or []

        permission_ids = []
        for rol in user_roles:
            perms = (rol or {}).get("permisos") or (rol or {}).get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permission_ids.append(perm.get("id"))

        return required_permission_id in permission_ids

    @action(detail=True, methods=["get"], url_path="employee_contract_detail")
    def employee_contract_detail(self, request, pk=None):
        """Devuelve el detalle completo de un contrato de empleado."""

        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        required_permission = 181
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para consultar contratos de empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            contract = (
                EmployeeContract.objects.select_related(
                    "id_employee_charge",
                    "id_employee_department",
                    "id_employee",
                    "contract_type",
                    "workday_type",
                    "work_mode_type",
                    "currency_type",
                    "contract_status",
                    "id_responsible_user",
                )
                .prefetch_related(
                    "contract_payments",
                    "contract_payments__id_day_of_week",
                    "employee_contract_deductions",
                    "employee_contract_deductions__deduction_type",
                    "employee_contract_increases",
                    "employee_contract_increases__increase_type",
                )
                .get(contract_code=pk)
            )
        except EmployeeContract.DoesNotExist:
            return Response(
                {"message": "No se encontró el contrato de empleado especificado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error("Error al obtener detalle de contrato de empleado", exc_info=True)
            return Response(
                {
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = EmployeeContractDetailSerializer(contract)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="latest_employee_contract")
    def latest_employee_contract(self, request, pk=None):
        """Devuelve el contrato más reciente asociado a un empleado."""

        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        required_permission = 181
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para consultar contratos de empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            contract = (
                EmployeeContract.objects.filter(id_employee_id=pk)
                .select_related(
                    "id_employee_charge",
                    "id_employee_department",
                    "id_employee",
                    "contract_type",
                    "workday_type",
                    "work_mode_type",
                    "currency_type",
                    "contract_status",
                    "id_responsible_user",
                )
                .prefetch_related(
                    "contract_payments",
                    "contract_payments__id_day_of_week",
                    "employee_contract_deductions",
                    "employee_contract_deductions__deduction_type",
                    "employee_contract_increases",
                    "employee_contract_increases__increase_type",
                )
                .order_by("-creation_date")
                .first()
            )
        except Exception as exc:
            logger.error("Error al obtener el contrato más reciente del empleado", exc_info=True)
            return Response(
                {
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not contract:
            return Response(
                {"message": "El empleado no tiene contratos registrados."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EmployeeContractDetailSerializer(contract)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        required_permission = 3

        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para crear empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = EmployeeWithContractCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = serializer.save()
        except DRFValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Error al crear empleado y contrato")
            return Response(
                {
                    "message": "Ocurrió un error al crear el empleado con su contrato.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Empleado y contrato creados exitosamente.",
                "data": result,
            },
            status=status.HTTP_201_CREATED,
        )
