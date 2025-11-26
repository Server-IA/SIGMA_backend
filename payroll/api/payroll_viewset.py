import logging
from datetime import datetime

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError

from payroll.models import Payroll, EmployeeContractDeduction, EmployeeContractIncrease
from payroll.serializers.payroll_serializers.payroll_masive_generetion_serializer import PayrollMasiveGenerationSerializer
from payroll.utils.payroll_document_generator import PayrollDocumentGenerator
from payroll.utils.audit_helpers import get_actor_info
from service_requests.utils.external_user_helper import get_users_info_batch, get_user_display_name
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
        
    def _get_responsible_user(self, request):
        user_id = getattr(request.user, "id", None)
        if not user_id:
            return None
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        Descarga una nómina en formato PDF.

        GET /api/payroll/{id_payroll}/download/

        Requiere permiso: 191 (payroll.download)

        Respuestas:
        - 200: PDF generado exitosamente
        - 401: Usuario no autenticado
        - 403: Sin permisos
        - 404: Nómina no encontrada
        - 500: Error interno
        """
        # Verificar autenticación
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permiso
        required_permission = 191
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para descargar nóminas."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener la nómina con relaciones optimizadas
            try:
                payroll = Payroll.objects.select_related(
                    'id_employee',
                    'id_employee__id_user',
                    'id_employee__id_employee_charge',
                    'id_employee_contract',
                    'id_employee_contract__id_employee_charge',
                    'currency_type',
                    'id_responsible_user'
                ).prefetch_related(
                    'payroll_deductions',
                    'payroll_deductions__deduction_type',
                    'payroll_increases',
                    'payroll_increases__increase_type'
                ).get(pk=pk)
            except Payroll.DoesNotExist:
                return Response(
                    {"message": "Nómina no encontrada."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Obtener el contrato asociado
            contract = payroll.id_employee_contract

            # Obtener deducciones e incrementos del contrato
            contract_deductions = EmployeeContractDeduction.objects.filter(
                employee_contracts_contract_code=contract
            ).select_related('deduction_type')

            contract_increases = EmployeeContractIncrease.objects.filter(
                employee_contracts_contract_code=contract
            ).select_related('increase_type')

            # Obtener datos del empleado desde servicio externo
            employee = payroll.id_employee
            employee_data = {}
            if employee and employee.id_user_id:
                users_data = get_users_info_batch([employee.id_user_id], request)
                employee_data = users_data.get(employee.id_user_id, {})

            # Obtener información del autor (usuario responsable)
            author_name = None
            responsible_user = payroll.id_responsible_user
            if responsible_user:
                responsible_user_id = getattr(responsible_user, 'id_user', None)
                if responsible_user_id:
                    author_data = get_users_info_batch([responsible_user_id], request)
                    author_user_data = author_data.get(responsible_user_id, {})
                    author_name = get_user_display_name(author_user_data)

            # Obtener información del usuario que descarga
            downloader_user = None
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                downloader_user = actor_name
            except Exception:
                downloader_user = None

            # Generar PDF
            pdf_bytes = PayrollDocumentGenerator.generate_pdf(
                payroll=payroll,
                employee_data=employee_data,
                contract=contract,
                contract_increases=contract_increases,
                contract_deductions=contract_deductions,
                author_name=author_name,
                downloader_user=downloader_user,
                logo_path=None
            )

            # Generar nombre del archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nomina_{payroll.id_payroll}_{timestamp}.pdf"

            # Retornar el PDF como respuesta
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as exc:
            logger.exception(f"Error generando PDF de nómina {pk}")
            return Response(
                {
                    "success": False,
                    "message": "Error al generar el PDF de la nómina.",
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )