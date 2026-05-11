import logging
import os
import json
import requests
from decimal import Decimal
from datetime import datetime, date

from django.db import transaction, connections, DatabaseError
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError

from payroll.models import Payroll
from users.authentication import JWTAuthentication

from payroll.models import Payroll, EmployeeContractDeduction, EmployeeContractIncrease
from service_requests.models import PaymentMethod
from payroll.serializers.payroll_serializers.payroll_history_report_serializer import PayrollHistoryReportSerializer
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

    @action(detail=False, methods=["post"], url_path="generate-history-report")
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
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                downloader_user = actor_name
            except Exception:
                downloader_user = None

            # 8. Generar PDF
            from core.services.pdf_service_payroll_history import build_payroll_history_pdf

            pdf_bytes = build_payroll_history_pdf(
                employee_info=employee_info,
                payroll_items=payroll_items,
                downloader_user=downloader_user,
                date_from=date_from,
                date_to=date_to,
            )

            # 9. Registrar auditoría
            try:
                download_timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                meta = {
                    "action": "download",
                    "report_type": "PAYROLL_HISTORY",
                    "employee_identification": document,
                    "date_from": str(date_from),
                    "date_to": str(date_to),
                    "download_timestamp": download_timestamp,
                }

                AuditClient(request).create(
                    object_id=str(employee_info.get("id_employee")),
                    after={"employee": employee_info, "meta": meta},
                    actor_id=actor_id or "Sistema",
                    actor_name=actor_name or "Sistema",
                    actor_role=actor_role_name or "Usuario",
                    permission_id=required_permission,
                    module="payroll",
                    submodule="payroll_history_report",
                )
            except Exception as audit_exc:
                logger.warning(
                    "El servicio de auditoría ha fallado al registrar descarga del informe de historial de nómina: %s",
                    str(audit_exc),
                )

            # 10. Construir respuesta HTTP con PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ident_safe = employee_info.get("identification") or document
            filename = f"Informe_Nomina_{ident_safe}_{timestamp}.pdf"

            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response["Content-Length"] = len(pdf_bytes)
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

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
                    'currency_type',
                    'status',
                    'payment_method'
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

# ==================================================================================================
# RF-INT-35 - Obtención de eventos económicos de Nómina en SIGMA mediante API REST
# Método: GET
# Seguridad: solo autenticación JWT, sin validación de permisos
# Respuesta normal: formato AAEF directo
# ==================================================================================================

SIGMA_DB_ALIAS_DEFAULT = os.getenv("SIGMA_DB_ALIAS", "default")
AGROFUSION_DB_ALIAS_DEFAULT = os.getenv("AGROFUSION_DB_ALIAS", "default")


def _rf35_to_jsonable(value):
    """
    Convierte Decimal/date/datetime/list/dict a tipos serializables por JSON.
    """
    if isinstance(value, Decimal):
        return float(value.quantize(Decimal("0.01")))

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: _rf35_to_jsonable(val) for key, val in value.items()}

    if isinstance(value, list):
        return [_rf35_to_jsonable(item) for item in value]

    if isinstance(value, tuple):
        return [_rf35_to_jsonable(item) for item in value]

    return value


def _rf35_json_response(payload, http_status=status.HTTP_200_OK):
    return JsonResponse(
        _rf35_to_jsonable(payload),
        status=http_status,
        safe=False,
        json_dumps_params={"ensure_ascii": False}
    )


def _rf35_error(message, http_status=status.HTTP_400_BAD_REQUEST, errors=None):
    payload = {
        "success": False,
        "message": message
    }

    if errors:
        payload["errors"] = errors

    return _rf35_json_response(payload, http_status)


def _rf35_authenticate_request(request):
    """
    Autenticación JWT manual.
    No valida permisos. Solo autenticación.
    """
    jwt_auth = JWTAuthentication()

    try:
        user_data = jwt_auth.authenticate(request)

        if user_data:
            user, payload = user_data
            request.user = user
            request.auth = payload

    except Exception as exc:
        logger.warning("[RF-INT-35] Error autenticando JWT: %s", exc)
        return False

    return bool(
        getattr(request, "user", None)
        and getattr(request.user, "is_authenticated", False)
    )


def _rf35_load_params(request):
    """
    RF-INT-35 se consume por GET.
    Las fechas llegan por path params y los extras por query string.
    """
    params = {}

    for key, value in request.GET.items():
        params[key] = value

    return params


def _rf35_parse_bool(value):
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    value_text = str(value).strip().lower()

    return value_text in ("1", "true", "yes", "si", "sí", "y")


def _rf35_parse_date(value, field_name):
    if not value:
        raise ValueError(f"El campo '{field_name}' es obligatorio.")

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    value_text = str(value).strip()

    try:
        return datetime.strptime(value_text[:10], "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"El campo '{field_name}' debe tener formato YYYY-MM-DD.")


def _rf35_decimal(value, default="0.00"):
    if value is None or value == "":
        return Decimal(default)

    return Decimal(str(value))


def _rf35_money(value):
    return _rf35_decimal(value).quantize(Decimal("0.01"))


def _rf35_date_iso(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    return str(value)[:10]


def _rf35_now_iso():
    return timezone.now().isoformat()


def _rf35_build_exchange_id(params):
    explicit = (
        params.get("ExchangeId")
        or params.get("exchangeId")
        or params.get("exchange_id")
    )

    if explicit:
        return str(explicit).strip()

    now = timezone.now()
    suffix = int(datetime.now().timestamp() * 1000) % 100000

    return f"AF-{now:%Y-%m}-{suffix:05d}"


def _rf35_fetch_all_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _rf35_get_connection(alias):
    if alias not in connections.databases:
        raise ValueError(
            f"No existe la conexión '{alias}' en settings.DATABASES. "
            f"Configura SIGMA_DB_ALIAS o AGROFUSION_DB_ALIAS según corresponda."
        )

    return connections[alias]


def _rf35_invoice_status_from_payroll(payroll):
    """
    Mapea estados Sigma hacia estado AAEF del invoice.
    """
    try:
        status_id = int(payroll.get("status_id"))
    except (TypeError, ValueError):
        return "UNKNOWN"

    if status_id == 18:
        return "PAID"

    if status_id == 16:
        return "PENDING"

    if status_id == 17:
        return "PARTIAL"

    return "UNKNOWN"


def _rf35_transaction_status_from_payroll(payroll):
    """
    Mapea estados Sigma hacia estado AAEF de transaction.
    """
    try:
        status_id = int(payroll.get("status_id"))
    except (TypeError, ValueError):
        return "UNKNOWN"

    if status_id == 18:
        return "COMPLETED"

    if status_id == 16:
        return "PENDING"

    if status_id == 17:
        return "PARTIAL"

    return "UNKNOWN"


def _rf35_should_build_transaction(payroll):
    """
    Se genera transaction para todas las nóminas consultadas:
    - 18 Pagado
    - 16 Pendiente
    - 17 Parcial
    """
    try:
        status_id = int(payroll.get("status_id"))
    except (TypeError, ValueError):
        return False

    return status_id in (16, 17, 18)


def _rf35_effective_transaction_date(payroll):
    """
    Para pagadas usa date_payment.
    Para pendientes/parciales, si no existe date_payment, usa end_date.
    """
    return payroll.get("date_payment") or payroll.get("end_date")


def _rf35_fetch_candidate_payrolls(connection, since_period, until_period):
    """
    Consulta nóminas por rango usando la estructura real actual.

    Confirmado:
    - payrolls.date_payment existe.
    - payrolls.payment_method_id existe y referencia payment_methods.code.
    - payrolls.status_id existe.
    - Se consultan estados 16, 17 y 18.
    """
    sql = """
        SELECT
            p.id_payroll,
            p.id_employee_contract,
            p.id_employee,
            p.start_date,
            p.end_date,
            p.base_salary AS salary_base,
            p.net_pay,
            p.total_increments,
            p.total_deductions,

            p.date_payment AS date_payment,

            p.payment_method_id AS payment_method_id,
            COALESCE(pm.code, p.payment_method_id, 'N/A') AS payment_method_code,
            pm.name AS payment_method_name,

            p.currency_type,
            p.status_id,
            st.name AS status_name,

            ec.contract_code,

            emp.email AS employee_email,

            au.username AS employee_document_number,
            au.first_name AS employee_first_name,
            au.last_name AS employee_last_name,
            au.email AS auth_email,

            un.symbol AS currency_code

        FROM payrolls p

        LEFT JOIN payment_methods pm
            ON pm.code = p.payment_method_id

        LEFT JOIN statues st
            ON st.id_statues = p.status_id

        LEFT JOIN employee_contracts ec
            ON ec.contract_code = p.id_employee_contract

        LEFT JOIN employees emp
            ON emp.id_employee = p.id_employee

        LEFT JOIN users usr
            ON usr.id_user = emp.id_user

        LEFT JOIN auth_user au
            ON au.id = usr.id_user

        LEFT JOIN units un
            ON un.id_units = p.currency_type

        WHERE p.start_date >= %s
          AND p.end_date <= %s
          AND p.status_id IN (16, 17, 18)

        ORDER BY p.start_date, p.end_date, p.id_payroll
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [since_period, until_period])
        return _rf35_fetch_all_dicts(cursor)


def _rf35_validate_payroll_totals(connection, id_payroll):
    """
    Valida con detalle real:

    SUM(payroll_increases.calculated_amount)
    -
    SUM(payroll_deductions.calculated_amount)
    =
    payrolls.net_pay

    En modo normal genera advertencia si no cuadra, pero NO bloquea.
    Solo bloquea si envías strictValidation=true.
    """
    sql = """
        SELECT
            p.id_payroll,
            p.net_pay,
            p.total_increments,
            p.total_deductions,

            COALESCE(inc.suma_ingresos, 0) AS suma_ingresos,
            COALESCE(ded.suma_deducciones, 0) AS suma_deducciones,

            COALESCE(inc.suma_ingresos, 0)
            - COALESCE(ded.suma_deducciones, 0) AS neto_calculado

        FROM payrolls p

        LEFT JOIN (
            SELECT
                id_payroll,
                SUM(calculated_amount) AS suma_ingresos
            FROM payroll_increases
            WHERE id_payroll = %s
            GROUP BY id_payroll
        ) inc
            ON inc.id_payroll = p.id_payroll

        LEFT JOIN (
            SELECT
                id_payroll,
                SUM(calculated_amount) AS suma_deducciones
            FROM payroll_deductions
            WHERE id_payroll = %s
            GROUP BY id_payroll
        ) ded
            ON ded.id_payroll = p.id_payroll

        WHERE p.id_payroll = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [id_payroll, id_payroll, id_payroll])
        rows = _rf35_fetch_all_dicts(cursor)

    if not rows:
        raise ValueError(f"No se encontró la nómina {id_payroll} para validar totales.")

    row = rows[0]

    net_pay = _rf35_money(row.get("net_pay"))
    neto_calculado = _rf35_money(row.get("neto_calculado"))
    delta = abs(neto_calculado - net_pay)

    return {
        "id_payroll": row.get("id_payroll"),
        "net_pay": net_pay,
        "total_increments": _rf35_money(row.get("total_increments")),
        "total_deductions": _rf35_money(row.get("total_deductions")),
        "suma_ingresos": _rf35_money(row.get("suma_ingresos")),
        "suma_deducciones": _rf35_money(row.get("suma_deducciones")),
        "neto_calculado": neto_calculado,
        "delta": delta
    }


def _rf35_fetch_payroll_lines(connection, id_payroll):
    """
    Obtiene líneas de ingresos y deducciones desde payroll_increases/payroll_deductions + types.

    Estructura real confirmada:
    - payroll_increases tiene increase_type, description, calculated_amount, id_payroll.
    - payroll_deductions tiene deduction_type, description, calculated_amount, id_payroll.
    - types tiene id_types, name, description.
    - types NO tiene debit_account_code ni credit_account_code.

    Por eso debit_account_code y credit_account_code se retornan como NULL.
    El JSON final enviará AccountingAccount como [].
    """
    sql = """
        SELECT
            'ingreso' AS line_type,
            t.id_types AS code,
            t.name AS name,
            COALESCE(NULLIF(pi.description, ''), t.description, t.name) AS description,
            CAST(NULL AS VARCHAR) AS debit_account_code,
            CAST(NULL AS VARCHAR) AS credit_account_code,
            pi.calculated_amount AS calculated_amount
        FROM payroll_increases pi
        LEFT JOIN types t
            ON t.id_types = pi.increase_type
        WHERE pi.id_payroll = %s

        UNION ALL

        SELECT
            'deduccion' AS line_type,
            t.id_types AS code,
            t.name AS name,
            COALESCE(NULLIF(pd.description, ''), t.description, t.name) AS description,
            CAST(NULL AS VARCHAR) AS debit_account_code,
            CAST(NULL AS VARCHAR) AS credit_account_code,
            pd.calculated_amount AS calculated_amount
        FROM payroll_deductions pd
        LEFT JOIN types t
            ON t.id_types = pd.deduction_type
        WHERE pd.id_payroll = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [id_payroll, id_payroll])
        return _rf35_fetch_all_dicts(cursor)


def _rf35_build_lines(raw_lines):
    lines = []

    for item in raw_lines:
        line_type = item.get("line_type")
        amount = _rf35_money(item.get("calculated_amount"))
        name = item.get("name") or str(item.get("code") or "")
        description = item.get("description") or name

        if line_type == "ingreso":
            accounting_account = item.get("debit_account_code")
        else:
            accounting_account = item.get("credit_account_code")

        lines.append({
            "Code": str(item.get("code") or ""),
            "Name": name,
            "Description": description,
            "LineType": line_type,
            "AccountingAccount": [str(accounting_account)] if accounting_account else [],
            "Quantity": 1,
            "UnitPrice": amount,
            "Value": amount,
            "Taxes": []
        })

    return lines


def _rf35_build_fallback_lines(payroll):
    """
    Construye líneas mínimas cuando payroll_increases/payroll_deductions no tienen detalle.
    """
    lines = []

    total_increments = _rf35_money(payroll.get("total_increments"))
    total_deductions = _rf35_money(payroll.get("total_deductions"))

    if total_increments > Decimal("0.00"):
        lines.append({
            "Code": "TOTAL_INGRESOS",
            "Name": "Total ingresos nómina",
            "Description": "Total de ingresos tomado desde payrolls.total_increments",
            "LineType": "ingreso",
            "AccountingAccount": [],
            "Quantity": 1,
            "UnitPrice": total_increments,
            "Value": total_increments,
            "Taxes": []
        })

    if total_deductions > Decimal("0.00"):
        lines.append({
            "Code": "TOTAL_DEDUCCIONES",
            "Name": "Total deducciones nómina",
            "Description": "Total de deducciones tomado desde payrolls.total_deductions",
            "LineType": "deduccion",
            "AccountingAccount": [],
            "Quantity": 1,
            "UnitPrice": total_deductions,
            "Value": total_deductions,
            "Taxes": []
        })

    return lines


def _rf35_get_table_columns(connection, table_name):
    try:
        with connection.cursor() as cursor:
            table_names = connection.introspection.table_names(cursor)

            if table_name not in table_names:
                return set()

            description = connection.introspection.get_table_description(cursor, table_name)

            return {
                getattr(column, "name", column[0])
                for column in description
            }

    except Exception as exc:
        logger.warning("[RF-INT-35] No se pudieron obtener columnas de %s: %s", table_name, exc)
        return set()


def _rf35_dynamic_insert(connection, table_name, data):
    """
    Inserta solo las columnas existentes en la tabla.
    Si la tabla o columnas no existen, no rompe el flujo.
    """
    columns = _rf35_get_table_columns(connection, table_name)

    if not columns:
        logger.warning("[RF-INT-35] Tabla %s no encontrada o sin columnas visibles.", table_name)
        return False

    filtered = {
        key: value
        for key, value in data.items()
        if key in columns
    }

    if not filtered:
        logger.warning("[RF-INT-35] No hay columnas compatibles para insertar en %s.", table_name)
        return False

    quoted_table = connection.ops.quote_name(table_name)
    quoted_columns = ", ".join(connection.ops.quote_name(column) for column in filtered.keys())
    placeholders = ", ".join(["%s"] * len(filtered))

    sql = f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({placeholders})"

    values = []

    for value in filtered.values():
        if isinstance(value, (dict, list)):
            values.append(json.dumps(_rf35_to_jsonable(value), ensure_ascii=False))
        elif isinstance(value, Decimal):
            values.append(str(value))
        else:
            values.append(value)

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)

        return True

    except Exception as exc:
        logger.warning("[RF-INT-35] No se pudo insertar en %s: %s", table_name, exc)
        return False


def _rf35_get_existing_idempotency_keys(connection, idempotency_keys):
    """
    Busca idempotency_key en af_audit_receipts si existe la tabla y columna.
    """
    if not idempotency_keys:
        return set()

    table_name = os.getenv("RF35_AUDIT_RECEIPTS_TABLE", "af_audit_receipts")
    columns = _rf35_get_table_columns(connection, table_name)

    if "idempotency_key" not in columns:
        logger.warning("[RF-INT-35] %s no tiene columna idempotency_key. No se validó idempotencia.", table_name)
        return set()

    placeholders = ", ".join(["%s"] * len(idempotency_keys))
    quoted_table = connection.ops.quote_name(table_name)

    sql = f"""
        SELECT idempotency_key
        FROM {quoted_table}
        WHERE idempotency_key IN ({placeholders})
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, list(idempotency_keys))
            rows = cursor.fetchall()

        return {row[0] for row in rows}

    except Exception as exc:
        logger.warning("[RF-INT-35] Error consultando idempotencia: %s", exc)
        return set()


def _rf35_register_audit_receipt(
    connection,
    exchange_id,
    document_id,
    idempotency_key,
    receipt_status,
    payload=None,
    error_message=None
):
    table_name = os.getenv("RF35_AUDIT_RECEIPTS_TABLE", "af_audit_receipts")
    now = timezone.now()

    data = {
        "idempotency_key": idempotency_key,
        "exchange_id": exchange_id,
        "document_id": document_id,
        "source_system": "Sigma",
        "status": receipt_status,
        "receipt_status": receipt_status,
        "payload_json": payload or {},
        "error_message": error_message,
        "created_at": now,
        "updated_at": now
    }

    return _rf35_dynamic_insert(connection, table_name, data)


def _rf35_register_accounting_transfer(connection, exchange_id, transfer_status, aaef_payload, error_message=None):
    table_name = os.getenv("RF35_ACCOUNTING_TRANSFERS_TABLE", "af_accounting_transfers")
    now = timezone.now()

    data = {
        "exchange_id": exchange_id,
        "transfer_status": transfer_status,
        "source_system": "Sigma",
        "payload_json": aaef_payload,
        "error_message": error_message,
        "is_update": False,
        "created_at": now,
        "updated_at": now
    }

    return _rf35_dynamic_insert(connection, table_name, data)


def _rf35_build_invoice(payroll, lines):
    id_payroll = payroll.get("id_payroll")
    id_employee_contract = payroll.get("id_employee_contract")
    document_id = f"{id_employee_contract}-{id_payroll}"

    first_name = payroll.get("employee_first_name") or ""
    last_name = payroll.get("employee_last_name") or ""
    employee_name = f"{first_name} {last_name}".strip()

    document_number = payroll.get("employee_document_number") or ""
    employee_email = payroll.get("auth_email") or payroll.get("employee_email") or ""

    invoice_status = _rf35_invoice_status_from_payroll(payroll)
    net_pay = _rf35_money(payroll.get("net_pay"))

    return {
        "Header": {
            "DocumentId": document_id,
            "Prefix": "NOM",
            "Serial": str(id_payroll),
            "IssueDate": _rf35_date_iso(payroll.get("start_date")),
            "DueDate": _rf35_date_iso(payroll.get("end_date")),
            "Status": invoice_status
        },
        "ThirdParty": {
            "DocumentNumber": str(document_number),
            "DocumentType": "CC",
            "Name": employee_name,
            "Email": employee_email
        },
        "Totals": {
            "Subtotal": _rf35_money(payroll.get("total_increments")),
            "TotalVAT": Decimal("0.00"),
            "TotalWithholdings": _rf35_money(payroll.get("total_deductions")),
            "TotalDiscounts": Decimal("0.00"),
            "TotalPayment": net_pay,
            "OutstandingBalance": Decimal("0.00") if invoice_status == "PAID" and payroll.get("date_payment") else net_pay
        },
        "Lines": lines
    }


def _rf35_build_transaction(payroll, issuer_info):
    id_payroll = payroll.get("id_payroll")
    id_employee_contract = payroll.get("id_employee_contract")

    effective_payment_date = _rf35_effective_transaction_date(payroll)
    payment_date = _rf35_date_iso(effective_payment_date)

    invoice_document_id = f"{id_employee_contract}-{id_payroll}"
    payment_document_id = f"PAY-{id_employee_contract}-{id_payroll}-{payment_date}"

    payment_method_code = (
        payroll.get("payment_method_code")
        or payroll.get("payment_method_id")
        or "N/A"
    )

    return {
        "DocumentId": payment_document_id,
        "Date": payment_date,
        "RelatedInvoiceId": invoice_document_id,
        "ThirdParty": {
            "NIT": issuer_info.get("NIT"),
            "Name": issuer_info.get("Name")
        },
        "Amount": _rf35_money(payroll.get("net_pay")),
        "Currency": payroll.get("currency_code") or "COP",
        "Status": _rf35_transaction_status_from_payroll(payroll),
        "Notes": (
            f"Contrato: {id_employee_contract} | "
            f"Período: {_rf35_date_iso(payroll.get('start_date'))} / {_rf35_date_iso(payroll.get('end_date'))}"
        ),
        "UpdatedAt": payment_date,
        "Type": {
            "Code": "PAY",
            "Name": "Pago de Nómina"
        },
        "PaymentMethod": {
            "Code": str(payment_method_code)
        }
    }


def _rf35_build_metadata(params, exchange_id, since_period, until_period):
    return {
        "ExchangeId": exchange_id,
        "GeneratedAt": _rf35_now_iso(),
        "StandardVersion": "1.0",
        "RequestedPeriod": {
            "From": since_period.isoformat(),
            "To": until_period.isoformat()
        },
        "SourceSystem": {
            "SystemId": params.get("systemId") or os.getenv("SIGMA_SYSTEM_ID", "sigma-prod-01"),
            "SystemName": "Sigma",
            "SystemNIT": params.get("systemNit") or os.getenv("SIGMA_SYSTEM_NIT", "900123456"),
            "Environment": params.get("environment") or os.getenv("SIGMA_ENVIRONMENT", "production")
        },
        "GeneratedBy": params.get("generatedBy") or os.getenv("SIGMA_GENERATED_BY", "agrofusion-integration-service")
    }


def _rf35_build_summary(included_payrolls, invoices, transactions):
    total_gross = sum(
        (_rf35_money(item.get("total_increments")) for item in included_payrolls),
        Decimal("0.00")
    )

    total_taxes = sum(
        (_rf35_money(item.get("total_deductions")) for item in included_payrolls),
        Decimal("0.00")
    )

    total_net = sum(
        (_rf35_money(item.get("net_pay")) for item in included_payrolls),
        Decimal("0.00")
    )

    currencies = {
        item.get("currency_code")
        for item in included_payrolls
        if item.get("currency_code")
    }

    currency = "COP"

    if currencies:
        currency = sorted(currencies)[0]

    if len(currencies) > 1:
        logger.warning("[RF-INT-35] Se encontraron múltiples monedas en el lote: %s", currencies)

    return {
        "TotalDocuments": len(invoices) + len(transactions),
        "TotalInvoices": len(invoices),
        "TotalTransactions": len(transactions),
        "TotalGrossAmount": total_gross,
        "TotalTaxes": total_taxes,
        "TotalNet": total_net,
        "Currency": currency
    }


def _rf35_build_accounting_headers(request, params):
    headers = {
        "Content-Type": "application/json"
    }

    explicit_token = (
        params.get("accounting_token")
        or params.get("accountingToken")
        or os.getenv("ACCOUNTING_BEARER_TOKEN")
    )

    if explicit_token:
        token_text = str(explicit_token).strip()
        headers["Authorization"] = token_text if token_text.lower().startswith("bearer ") else f"Bearer {token_text}"
        return headers

    auth_header = getattr(request, "META", {}).get("HTTP_AUTHORIZATION")

    if not auth_header and hasattr(request, "headers"):
        auth_header = request.headers.get("Authorization")

    if auth_header:
        headers["Authorization"] = auth_header

    return headers


def _rf35_send_to_accounting(request, params, aaef_payload):
    """
    Envío opcional al sistema contable.
    Para activarlo:
    ?send_to_accounting=true
    """
    health_url = (
        params.get("accounting_health_url")
        or params.get("accountingHealthUrl")
        or os.getenv("ACCOUNTING_HEALTH_URL")
    )

    aaef_url = (
        params.get("accounting_aaef_url")
        or params.get("accountingAaefUrl")
        or os.getenv("ACCOUNTING_AAEF_URL")
    )

    headers = _rf35_build_accounting_headers(request, params)

    if health_url:
        health_response = requests.get(health_url, headers=headers, timeout=30)

        if health_response.status_code != 200:
            return {
                "sent": False,
                "status_code": health_response.status_code,
                "message": "El health check del sistema contable no retornó HTTP 200.",
                "response": health_response.text[:500]
            }

    if not aaef_url:
        return {
            "sent": False,
            "status_code": None,
            "message": "ACCOUNTING_AAEF_URL no está configurada."
        }

    response = requests.post(
        aaef_url,
        json=_rf35_to_jsonable(aaef_payload),
        headers=headers,
        timeout=60
    )

    return {
        "sent": response.status_code in (200, 201, 202),
        "status_code": response.status_code,
        "message": "Lote enviado al sistema contable."
        if response.status_code in (200, 201, 202)
        else "El sistema contable rechazó el lote.",
        "response": response.text[:1000]
    }


@csrf_exempt
@require_http_methods(["GET"])
def consult_sigma_economic_events(request, sincePeriod=None, untilPeriod=None):
    """
    RF-INT-35
    Obtención de eventos económicos de Nómina en SIGMA mediante API REST.

    Ejemplo:
    GET /payroll/economic-events/consult/2025-11-01/2025-11-30/

    Query params opcionales:
    ?send_to_accounting=true
    ?tolerance=0.01
    ?exchangeId=AF-2026-04-000052
    ?debug=true
    ?strictValidation=true
    """
    if not _rf35_authenticate_request(request):
        return _rf35_error(
            "Usuario no autenticado.",
            status.HTTP_401_UNAUTHORIZED
        )

    try:
        params = _rf35_load_params(request)

        if sincePeriod:
            params["sincePeriod"] = sincePeriod

        if untilPeriod:
            params["untilPeriod"] = untilPeriod

        since_period = _rf35_parse_date(
            params.get("sincePeriod") or params.get("since_period"),
            "sincePeriod"
        )

        until_period = _rf35_parse_date(
            params.get("untilPeriod") or params.get("until_period"),
            "untilPeriod"
        )

        if since_period > until_period:
            return _rf35_error(
                "sincePeriod no puede ser mayor que untilPeriod.",
                status.HTTP_400_BAD_REQUEST
            )

        tolerance = _rf35_money(params.get("tolerance") or "0.01")

        strict_validation = _rf35_parse_bool(
            params.get("strictValidation")
            or params.get("strict_validation")
        )

        sigma_alias = (
            params.get("sigma_db_alias")
            or params.get("sigmaDbAlias")
            or SIGMA_DB_ALIAS_DEFAULT
        )

        agrofusion_alias = (
            params.get("agrofusion_db_alias")
            or params.get("agrofusionDbAlias")
            or AGROFUSION_DB_ALIAS_DEFAULT
        )

        sigma_connection = _rf35_get_connection(sigma_alias)
        agrofusion_connection = _rf35_get_connection(agrofusion_alias)

        exchange_id = _rf35_build_exchange_id(params)

        issuer_info = {
            "NIT": params.get("issuerNit") or os.getenv("SIGMA_ISSUER_NIT", "900123456"),
            "Name": params.get("issuerName") or os.getenv("SIGMA_ISSUER_NAME", "Empresa AgroFusion SA")
        }

        candidate_payrolls = _rf35_fetch_candidate_payrolls(
            sigma_connection,
            since_period,
            until_period
        )

        possible_idempotency_keys = []

        for payroll in candidate_payrolls:
            invoice_document_id = f"{payroll.get('id_employee_contract')}-{payroll.get('id_payroll')}"
            possible_idempotency_keys.append(f"{exchange_id}:{invoice_document_id}")

            if _rf35_should_build_transaction(payroll):
                payment_date = _rf35_date_iso(_rf35_effective_transaction_date(payroll))
                payment_document_id = f"PAY-{payroll.get('id_employee_contract')}-{payroll.get('id_payroll')}-{payment_date}"
                possible_idempotency_keys.append(f"{exchange_id}:{payment_document_id}")

        existing_keys = _rf35_get_existing_idempotency_keys(
            agrofusion_connection,
            possible_idempotency_keys
        )

        invoices = []
        transactions = []
        included_payrolls = []
        excluded = []
        warnings = []

        for payroll in candidate_payrolls:
            id_payroll = payroll.get("id_payroll")
            id_employee_contract = payroll.get("id_employee_contract")

            invoice_document_id = f"{id_employee_contract}-{id_payroll}"
            payment_date = _rf35_date_iso(_rf35_effective_transaction_date(payroll))
            payment_document_id = f"PAY-{id_employee_contract}-{id_payroll}-{payment_date}"

            invoice_key = f"{exchange_id}:{invoice_document_id}"
            payment_key = f"{exchange_id}:{payment_document_id}"

            if invoice_key in existing_keys:
                excluded_item = {
                    "id_payroll": id_payroll,
                    "document_id": invoice_document_id,
                    "reason": "DUPLICATE_IDEMPOTENCY_KEY",
                    "message": "Ya existe un invoice con el mismo ExchangeId + DocumentId en af_audit_receipts."
                }

                excluded.append(excluded_item)
                continue

            validation = _rf35_validate_payroll_totals(
                sigma_connection,
                id_payroll
            )

            if validation["delta"] > tolerance:
                warning_item = {
                    "id_payroll": id_payroll,
                    "document_id": invoice_document_id,
                    "reason": "NET_PAY_VALIDATION_WARNING",
                    "message": "La validación de suma de conceptos no coincide, pero el documento se incluirá porque strictValidation=false.",
                    "net_pay": validation["net_pay"],
                    "suma_ingresos": validation["suma_ingresos"],
                    "suma_deducciones": validation["suma_deducciones"],
                    "neto_calculado": validation["neto_calculado"],
                    "delta": validation["delta"],
                    "tolerance": tolerance
                }

                warnings.append(warning_item)

                _rf35_register_audit_receipt(
                    agrofusion_connection,
                    exchange_id,
                    invoice_document_id,
                    invoice_key,
                    "VALIDATION_WARNING",
                    payload=warning_item,
                    error_message=warning_item["message"]
                )

                if strict_validation:
                    excluded_item = warning_item.copy()
                    excluded_item["reason"] = "NET_PAY_VALIDATION_FAILED"
                    excluded_item["message"] = "La validación de suma de conceptos no coincide y strictValidation=true."

                    excluded.append(excluded_item)

                    _rf35_register_audit_receipt(
                        agrofusion_connection,
                        exchange_id,
                        invoice_document_id,
                        invoice_key,
                        "VALIDATION_FAILED",
                        payload=excluded_item,
                        error_message=excluded_item["message"]
                    )

                    continue

            raw_lines = _rf35_fetch_payroll_lines(
                sigma_connection,
                id_payroll
            )

            lines = _rf35_build_lines(raw_lines)

            if not lines:
                fallback_warning = {
                    "id_payroll": id_payroll,
                    "document_id": invoice_document_id,
                    "reason": "PAYROLL_WITHOUT_DETAIL_LINES",
                    "message": "La nómina no tiene líneas de detalle; se construirán líneas fallback desde payrolls.total_increments y payrolls.total_deductions."
                }

                warnings.append(fallback_warning)

                _rf35_register_audit_receipt(
                    agrofusion_connection,
                    exchange_id,
                    invoice_document_id,
                    invoice_key,
                    "LINES_FALLBACK",
                    payload=fallback_warning,
                    error_message=fallback_warning["message"]
                )

                lines = _rf35_build_fallback_lines(payroll)

            if not lines:
                excluded_item = {
                    "id_payroll": id_payroll,
                    "document_id": invoice_document_id,
                    "reason": "PAYROLL_WITHOUT_LINES",
                    "message": "La nómina no tiene líneas de detalle ni totales suficientes para construir líneas fallback."
                }

                excluded.append(excluded_item)

                _rf35_register_audit_receipt(
                    agrofusion_connection,
                    exchange_id,
                    invoice_document_id,
                    invoice_key,
                    "VALIDATION_FAILED",
                    payload=excluded_item,
                    error_message=excluded_item["message"]
                )

                continue

            invoice_payload = _rf35_build_invoice(payroll, lines)

            invoices.append(invoice_payload)
            included_payrolls.append(payroll)

            _rf35_register_audit_receipt(
                agrofusion_connection,
                exchange_id,
                invoice_document_id,
                invoice_key,
                "BUILT",
                payload=invoice_payload
            )

            if _rf35_should_build_transaction(payroll) and payment_key not in existing_keys:
                transaction_payload = _rf35_build_transaction(payroll, issuer_info)

                transactions.append(transaction_payload)

                _rf35_register_audit_receipt(
                    agrofusion_connection,
                    exchange_id,
                    payment_document_id,
                    payment_key,
                    "BUILT",
                    payload=transaction_payload
                )
            else:
                warning_item = {
                    "id_payroll": id_payroll,
                    "document_id": payment_document_id,
                    "status_id": payroll.get("status_id"),
                    "status_name": payroll.get("status_name"),
                    "reason": "TRANSACTION_NOT_CREATED",
                    "message": "No se genera transaction porque el estado no está mapeado o ya existe una transaction con el mismo ExchangeId + DocumentId."
                }

                warnings.append(warning_item)

                _rf35_register_audit_receipt(
                    agrofusion_connection,
                    exchange_id,
                    invoice_document_id,
                    invoice_key,
                    "TRANSACTION_SKIPPED",
                    payload=warning_item,
                    error_message=warning_item["message"]
                )

        aaef_payload = {
            "metadata": _rf35_build_metadata(
                params,
                exchange_id,
                since_period,
                until_period
            ),
            "summary": _rf35_build_summary(
                included_payrolls,
                invoices,
                transactions
            ),
            "invoices": invoices,
            "transactions": transactions
        }

        _rf35_register_accounting_transfer(
            agrofusion_connection,
            exchange_id,
            "BUILT",
            aaef_payload
        )

        send_to_accounting = _rf35_parse_bool(
            params.get("send_to_accounting")
            or params.get("sendToAccounting")
        )

        accounting_result = None

        if send_to_accounting:
            accounting_result = _rf35_send_to_accounting(
                request,
                params,
                aaef_payload
            )

            _rf35_register_accounting_transfer(
                agrofusion_connection,
                exchange_id,
                "SENT" if accounting_result.get("sent") else "FAILED",
                aaef_payload,
                error_message=None if accounting_result.get("sent") else accounting_result.get("message")
            )

        response_status = (
            status.HTTP_202_ACCEPTED
            if send_to_accounting and accounting_result and accounting_result.get("sent")
            else status.HTTP_200_OK
        )

        if _rf35_parse_bool(params.get("debug")):
            aaef_payload["debug"] = {
                "sigma_db_alias": sigma_alias,
                "agrofusion_db_alias": agrofusion_alias,
                "candidate_payrolls": len(candidate_payrolls),
                "included_payrolls": len(included_payrolls),
                "excluded_payrolls": len(excluded),
                "total_transactions": len(transactions),
                "tolerance": tolerance,
                "strict_validation": strict_validation,
                "sent_to_accounting": send_to_accounting,
                "warnings": warnings,
                "excluded": excluded
            }

            if accounting_result is not None:
                aaef_payload["debug"]["accounting_result"] = accounting_result

        return _rf35_json_response(
            aaef_payload,
            response_status
        )

    except ValueError as exc:
        return _rf35_error(
            str(exc),
            status.HTTP_400_BAD_REQUEST
        )

    except DatabaseError as exc:
        logger.error("[RF-INT-35] Error de base de datos: %s", exc, exc_info=True)
        return _rf35_error(
            "Error consultando la base de datos de Sigma.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            errors={"database": [str(exc)]}
        )

    except requests.RequestException as exc:
        logger.error("[RF-INT-35] Error HTTP contra sistema contable: %s", exc, exc_info=True)
        return _rf35_error(
            "Error comunicándose con el sistema contable.",
            status.HTTP_502_BAD_GATEWAY,
            errors={"external_service": [str(exc)]}
        )

    except Exception as exc:
        logger.error("[RF-INT-35] Error inesperado: %s", exc, exc_info=True)
        return _rf35_error(
            "Error interno procesando eventos económicos de nómina Sigma.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            errors={"detail": [str(exc)]}
        )