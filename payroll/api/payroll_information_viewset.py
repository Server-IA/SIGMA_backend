from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
import logging

from payroll.models import Payroll
from payroll.serializers.payroll_information_serializers.payroll_detail_serializer import (
    PayrollDetailSerializer,
)

logger = logging.getLogger(__name__)


class PayrollInformationViewSet(viewsets.ViewSet):
    """ViewSet para consultar información de nóminas."""
    
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

    @action(detail=True, methods=["get"], url_path="view-payroll-detail")
    def view_payroll_detail(self, request, pk=None):
        """
        Obtiene el detalle completo de una nómina.
        
        Incluye:
        - Información básica de la nómina
        - Documento del empleado (desde servicio externo)
        - Lista de deducciones (payroll_deductions)
        - Lista de incrementos (payroll_increases)
        
        Requiere permiso: 189 (payroll.view_payroll_detail)
        
        URL: GET /payroll-information/{id_payroll}/view-payroll-detail/
        """
        # Verificar autenticación
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verificar permiso
        required_permission = 190
        if not self.check_permission(request, required_permission):
            return Response(
                {"success": False, "message": "No tiene permisos para consultar el detalle de nómina."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Obtener la nómina con todas sus relaciones optimizadas
            payroll = (
                Payroll.objects.select_related(
                    'id_employee',
                    'id_employee__id_user',
                    'id_employee_contract',
                    'id_responsible_user'
                )
                .prefetch_related(
                    'payroll_deductions',
                    'payroll_deductions__deduction_type',
                    'payroll_increases',
                    'payroll_increases__increase_type'
                )
                .get(id_payroll=pk)
            )
        except Payroll.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Nómina no encontrada."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error("Error al obtener detalle de nómina: %s", str(exc), exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # Obtener datos del usuario desde servicio externo si el empleado tiene id_user
            # y también del usuario responsable
            users_data = {}
            user_ids = []
            
            # Obtener id_user del empleado
            employee = payroll.id_employee
            if employee and employee.id_user_id:
                user_ids.append(employee.id_user_id)
            
            # Obtener id_user del usuario responsable
            responsible_user = payroll.id_responsible_user
            if responsible_user and hasattr(responsible_user, 'id_user') and responsible_user.id_user:
                user_ids.append(responsible_user.id_user)
            
            # Obtener todos los usuarios en batch si hay alguno
            if user_ids:
                from service_requests.utils.external_user_helper import get_users_info_batch
                users_data = get_users_info_batch(user_ids, request)

            # Serializar la nómina
            serializer = PayrollDetailSerializer(
                payroll,
                context={'request': request, 'users_data': users_data}
            )

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            logger.error("Error al serializar detalle de nómina: %s", str(exc), exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

