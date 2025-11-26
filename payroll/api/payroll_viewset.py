import logging
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError

from payroll.models import Payroll
from payroll.serializers.payroll_serializers.payroll_masive_generetion_serializer import PayrollMasiveGenerationSerializer
from payroll.serializers.payroll_serializers.payroll_detail_serializer import PayrollDetailSerializer
from users.models.user import User

logger = logging.getLogger(__name__)

class PayrollViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de nóminas.
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

    @action(detail=False, methods=['post'], url_path='generate-massive')
    def generate_massive(self, request):
        """
        Endpoint para generar nómina masiva.
        
        POST /api/payroll/generate-massive/
        
        Body:
        {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "id_employee_department": 5,
            "id_employee_charge": 12,
            "batch_id": "550e8400-e29b-41d4-a716-446655440000",  // Opcional
            "exclude_conflicts": false,  // Opcional
            "employees": [
                {
                    "employee_id": 101,
                    "increases": [...],  // Opcional
                    "deductions": [...]  // Opcional
                }
            ]
        }
        
        Respuestas:
        - 201: Nóminas creadas exitosamente
        - 206: Nóminas creadas parcialmente (algunos empleados fallaron)
        - 400: Error de validación
        - 403: Sin permisos
        """
        # Verificar autenticación
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verificar permiso
        required_permission = 188
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para la gestión de nómina masiva."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        responsable_user = self._get_responsible_user(request)
        if responsable_user is None:
            return Response(
                {"message": "Usuario responsable no encontrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            serializer = PayrollMasiveGenerationSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)

            created_payrolls = serializer.save()
            
            # Verificar si hubo fallos parciales
            has_failures = any(
                hasattr(payroll, '_failed_employees') 
                for payroll in created_payrolls
            )
            
            if has_failures:
                # Obtener la lista de empleados fallidos del primer payroll que la tenga
                failed_employees = next(
                    (payroll._failed_employees for payroll in created_payrolls 
                        if hasattr(payroll, '_failed_employees')),
                    []
                )
                
                response_data = {
                    "success": True,
                    "message": f"Se generaron {len(created_payrolls)} nóminas, pero {len(failed_employees)} empleados fallaron.",
                    "data": {
                        "created_count": len(created_payrolls),
                        "failed_count": len(failed_employees),
                        "created_payrolls": [
                            {
                                "payroll_id": payroll.id_payroll,
                                "employee_id": payroll.id_employee_id,
                                "base_salary": float(payroll.base_salary),
                                "total_increments": float(payroll.total_increments),
                                "total_deductions": float(payroll.total_deductions),
                                "net_pay": float(payroll.net_pay),
                                "start_date": payroll.start_date.isoformat(),
                                "end_date": payroll.end_date.isoformat(),
                                "creation_date": payroll.creation_date.isoformat(),
                            }
                            for payroll in created_payrolls
                        ],
                        "failed_employees": failed_employees
                    }
                }
                
                return Response(
                    response_data,
                    status=status.HTTP_206_PARTIAL_CONTENT
                )
            
            # Éxito total
            response_data = {
                "success": True,
                "message": f"Nómina masiva generada correctamente. Se crearon {len(created_payrolls)} nóminas.",
                "data": {
                    "created_count": len(created_payrolls),
                    "created_payrolls": [
                        {
                            "payroll_id": payroll.id_payroll,
                            "employee_id": payroll.id_employee_id,
                            "base_salary": float(payroll.base_salary),
                            "total_increments": float(payroll.total_increments),
                            "total_deductions": float(payroll.total_deductions),
                            "net_pay": float(payroll.net_pay),
                            "start_date": payroll.start_date.isoformat(),
                            "end_date": payroll.end_date.isoformat(),
                            "creation_date": payroll.creation_date.isoformat(),
                        }
                        for payroll in created_payrolls
                    ]
                }
            }
            
            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )

        except DRFValidationError as exc:
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "errors": exc.detail
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        except Exception as exc:
            logger.exception("Error en carga masiva de ajustes")
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="view-payroll-detail")
    def view_payroll_detail(self, request, pk=None):
        """
        Obtiene el detalle completo de una nómina.
        
        Incluye:
        - Información básica de la nómina
        - Documento del empleado (desde servicio externo)
        - Lista de deducciones (payroll_deductions)
        - Lista de incrementos (payroll_increases)
        
        Requiere permiso: 190 (payroll.view_payroll_detail)
        
        URL: GET /payroll/{id_payroll}/view-payroll-detail/
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
                    'id_responsible_user',
                    'currency_type'
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
        
    def _get_responsible_user(self, request):
        user_id = getattr(request.user, "id", None)
        if not user_id:
            return None
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None