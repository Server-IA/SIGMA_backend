import logging
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError

from payroll.models import Payroll
from payroll.serializers.payroll_serializers.payroll_history_report_serializer import PayrollHistoryReportSerializer
from payroll.models import Payroll, EmployeeContractDeduction, EmployeeContractIncrease
from payroll.serializers.payroll_serializers.payroll_list_serializer import PayrollListSerializer
from payroll.serializers.payroll_serializers.payroll_masive_generetion_serializer import PayrollMasiveGenerationSerializer
from payroll.serializers.payroll_serializers.payroll_detail_serializer import PayrollDetailSerializer
from payroll.serializers.payroll_serializers.payroll_serializer import PayrollCreateSerializer
from payroll.services.payroll_history_service import (
    PayrollHistoryService,
    EmployeeNotFoundError,
)
from payroll.utils.audit_helpers import get_actor_info
from payroll.utils.payroll_document_generator import PayrollDocumentGenerator
from payroll.utils.audit_helpers import get_actor_info
from service_requests.utils.external_user_helper import get_users_info_batch, get_user_display_name
from users.models.user import User
from audit_sdk import AuditClient

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

    @action(detail=False, methods=['post'], url_path='generate-history-report')
    def generate_history_report(self, request):
        """Genera y descarga el PDF del historial de nóminas de un empleado.

        Requiere permiso: 194 (payroll.history_report)
        """
        # 1. Verificar autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 2. Verificar permiso
        required_permission = 194
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para generar informes de historial de nómina."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 3. Validar entrada
        serializer = PayrollHistoryReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Parámetros inválidos",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        document = data["employeeIdentification"]
        date_from = data["dateFrom"]
        date_to = data["dateTo"]

        try:
            # 4. Resolver empleado y user_data externo
            employee, user_data = PayrollHistoryService.resolve_employee_by_identification(
                document_number=document,
                request=request,
            )

            # 5. Consultar nóminas
            payroll_qs = PayrollHistoryService.get_payrolls_for_employee(
                employee=employee,
                date_from=date_from,
                date_to=date_to,
            )

            # 6. Construir payload para PDF
            employee_info, payroll_items = PayrollHistoryService.build_history_payload(
                employee=employee,
                user_data=user_data,
                payrolls=payroll_qs,
            )

            # 7. Obtener info de usuario que descarga
            downloader_user = None
            actor_id = None
            actor_name = None
            actor_role_name = None

            if hasattr(request, 'user') and request.user.is_authenticated:
                try:
                    downloader_user = User.objects.get(id=request.user.id)
                    actor_id = str(downloader_user.id)
                    actor_name = downloader_user.get_full_name() or downloader_user.email

                    # Obtener el rol del usuario desde el token
                    payload = getattr(request, "auth", None) or {}
                    user_roles = payload.get("rol") or payload.get("roles") or []
                    if user_roles and isinstance(user_roles, list) and len(user_roles) > 0:
                        actor_role_name = user_roles[0].get("nombre") or user_roles[0].get("name")
                except User.DoesNotExist:
                    pass

            # 8. Registrar evento de auditoría
            audit_client = AuditClient()
            audit_client.log_event(
                action="GENERATE_HISTORY_REPORT",
                resource_type="payroll_history",
                resource_id=f"employee_{document}",
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role_name,
                metadata={
                    "employee_document": document,
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                    "payroll_count": len(payroll_items),
                },
            )

            # 9. Generar PDF
            pdf_bytes = PayrollHistoryService.generate_pdf(
                employee=employee_info,
                payroll_items=payroll_items,
                date_from=date_from,
                date_to=date_to,
                downloader=downloader_user,
            )

            # 10. Crear respuesta con el PDF
            response = HttpResponse(
                pdf_bytes,
                content_type="application/pdf",
            )
            filename = f"historial_nomina_{document}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        except EmployeeNotFoundError as e:
            logger.error(f"Error generando historial de nómina: {str(e)}")
            return Response(
                {"message": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.exception("Error inesperado generando historial de nómina")
            return Response(
                {"message": "Error interno del servidor al generar el historial de nómina"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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

    @action(detail=False, methods=["get"], url_path="list-generated")
    def list_generated(self, request):
        """
        HU-NOM-005: Listar nóminas generadas.
        Permiso requerido: 193
        """

        # -----------------------
        # 1. Validación de permisos
        # -----------------------
        required_permission = 193
        if not self.check_permission(request, required_permission):
            return Response(
                {"success": False, "message": "No tiene permiso para ver las nóminas generadas."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # -----------------------
        # 2. Obtener todas las nóminas SIN filtros
        # -----------------------
        queryset = Payroll.objects.select_related(
            "id_employee",
            "id_employee__id_user",
            "id_responsible_user",
            "currency_type"
        ).all()

        # -----------------------
        # 3. Serializar y responder (SIN paginación)
        # -----------------------
        serializer = PayrollListSerializer(queryset, many=True, context={"request": request})

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='create-payroll')
    def create_payroll(self, request):
        """
        Endpoint para crear una nueva nómina.
        
        Requiere permiso: 195 (payroll.create_payroll)
        
        Body:
        {
            "id_employee": 1,
            "contract_code": "CONTRACT-001",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "additional_deductions": [  // Opcional
                {
                    "deduction_type": 1,
                    "amount_type": "Porcentaje",
                    "amount_value": 5.5,
                    "application_deduction_type": "SalarioBase",
                    "start_date_deduction": "2025-01-01",  // Opcional
                    "end_date_deductions": "2025-01-31",    // Opcional
                    "description": "Descuento por préstamo", // Opcional
                    "amount": 1                             // Opcional, por defecto 1
                }
            ],
            "additional_increases": [  // Opcional
                {
                    "increase_type": 1,
                    "amount_type": "fijo",
                    "amount_value": 100000,
                    "application_increase_type": "SalarioBase",
                    "start_date_increase": "2025-01-01",    // Opcional
                    "end_date_increase": "2025-01-31",      // Opcional
                    "description": "Bonificación",          // Opcional
                    "amount": 1                             // Opcional, por defecto 1
                }
            ]
        }
        """
        # Verificar autenticación
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verificar permiso
        required_permission = 195
        if not self.check_permission(request, required_permission):
            return Response(
                {"success": False, "message": "No tiene permisos para crear nóminas."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Usar el nuevo serializador
            serializer = PayrollCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            payroll = serializer.save()

            # Obtener datos del empleado para la respuesta
            employee = payroll.id_employee
            contract = payroll.id_employee_contract

            # Construir respuesta
            response_data = {
                "success": True,
                "message": "Nómina creada exitosamente",
                "data": {
                    "payroll_id": payroll.id_payroll,
                    "employee_id": employee.id_employee,
                    "contract_code": contract.contract_code,
                    "start_date": payroll.start_date.isoformat(),
                    "end_date": payroll.end_date.isoformat(),
                    "base_salary": float(payroll.base_salary),
                    "time_worked": float(payroll.time_worked),
                    "total_deductions": float(payroll.total_deductions),
                    "total_increments": float(payroll.total_increments),
                    "net_pay": float(payroll.net_pay),
                    "currency_type": {
                        "id": payroll.currency_type.id_units,
                        "name": payroll.currency_type.name
                    },
                    "creation_date": payroll.creation_date.isoformat(),
                    "responsible_user": {
                        "id": payroll.id_responsible_user.id_user,
                        "name": ""  # We'll update this after getting user data
                    }
                }
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except DRFValidationError as exc:
            logger.error(f"Error de validación al crear nómina: {str(exc)}")
            return Response(
                {
                    "success": False,
                    "message": "Error de validación en los datos de la nómina",
                    "errors": exc.detail
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Error inesperado al crear nómina")
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud de creación de nómina",
                    "error": str(exc)
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