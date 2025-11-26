import logging
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from payroll.serializers.payroll_history_report_serializer import PayrollHistoryReportSerializer
from payroll.services.payroll_history_service import (
    PayrollHistoryService,
    EmployeeNotFoundError,
)
from payroll.utils.audit_helpers import get_actor_info
from audit_sdk import AuditClient

logger = logging.getLogger(__name__)


class PayrollHistoryReportViewSet(viewsets.ViewSet):
    """Genera informe de historial de nóminas (HU-NOV-004)."""

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

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
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
            return Response(
                {
                    "success": False,
                    "message": str(e) or "El documento ingresado no se encuentra registrado en el sistema.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error("Error generando informe de historial de nóminas: %s", e, exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "No fue posible generar el informe. Intente nuevamente.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
