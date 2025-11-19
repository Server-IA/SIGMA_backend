import logging

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError

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
