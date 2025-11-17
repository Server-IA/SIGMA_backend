from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
import logging
from audit_sdk import AuditClient

from payroll.serializers.established_contracts_serializers.established_contract_serializer import (
    EstablishedContractCreateSerializer
)
from payroll.models.established_contract import EstablishedContract
from payroll.utils.audit_helpers import get_actor_info, contract_snapshot

logger = logging.getLogger(__name__)

class EstablishedContractViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de contratos establecidos.
    """
    
    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
        """
        # Obtener el payload del JWT desde request.auth
        payload = getattr(request, "auth", None) or {}

        # Obtener roles del payload (soporta "rol" y "roles")
        user_roles = payload.get("rol") or payload.get("roles") or []

        # Extraer todos los IDs de permisos de todos los roles
        permisos_usuario = []
        for rol in user_roles:
            # Obtener permisos del rol (soporta "permisos" y "permissions")
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))

        return required_permission_id in permisos_usuario

    @action(detail=False, methods=['post'], url_path='create_established_contract')
    def create_established_contract(self, request):
        """
        Crea un nuevo contrato establecido.
        
        Requiere permiso: 174 (established_contract.create)
        
        Campos obligatorios:
        - id_employee_charge: ID del cargo del empleado
        - contract_type: ID del tipo de contrato (debe pertenecer a la categoría 15)
        - start_date: Fecha de inicio del contrato
        - payment_frequency_type: Frecuencia de pago (diario, semanal, quincenal, mensual)
        - salary_base: Salario base (decimal mayor a 0)
        
        Campos condicionales:
        - Si cumulative_vacation es True, start_cumulative_vacation es obligatorio
        - Los campos de deducciones e incrementos deben tener fechas dentro del rango del contrato
        """
        try:
            # Verificar que el usuario esté autenticado
            if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
                return Response(
                    {"message": "Usuario no autenticado"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            permission_id = 174  # established_contract.create

            # Verificar permiso
            if not self.check_permission(request, permission_id):
                return Response(
                    {"message": "No tiene permisos para crear un contrato establecido."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Obtener datos del usuario para auditoría
            actor_id, actor_name, actor_role_name = get_actor_info(request.user)

            # Validar y crear el contrato
            serializer = EstablishedContractCreateSerializer(
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid():
                with transaction.atomic():
                    # Crear el contrato
                    contract = serializer.save()
                    
                    # Auditoría
                    try:
                        AuditClient(request).create(
                            object_id=str(contract.contract_code),
                            after=contract_snapshot(contract),
                            actor_id=actor_id,
                            actor_name=actor_name,
                            actor_role=actor_role_name,
                            permission_id=permission_id,
                            module="payroll",
                            submodule="established_contract",
                        )
                    except Exception as e:
                        logger.warning(
                            "El servicio de auditoría ha fallado en create_established_contract: %s", e
                        )
                    
                    return Response(
                        {
                            "success": True,
                            "message": "Contrato creado exitosamente",
                            "contract_code": contract.contract_code
                        },
                        status=status.HTTP_201_CREATED
                    )
            
            return Response(
                {
                    "success": False,
                    "message": "Error al crear el contrato",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error("Error al crear contrato: %s", str(e), exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor al procesar la solicitud",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
