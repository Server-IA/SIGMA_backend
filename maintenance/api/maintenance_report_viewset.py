from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

from maintenance.models import MaintenanceReport, MaintenanceScheduling
from maintenance.serializers.maintenance_report_serializers import (
    MaintenanceReportCreateSerializer,
    MaintenanceReportListSerializer,
    MaintenanceReportDetailSerializer
)
from core.services.pdf_service import build_maintenance_report_pdf
from django.http import HttpResponse
import os
import requests

logger = logging.getLogger(__name__)


class MaintenanceReportViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de reportes de mantenimiento.
    """

    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
        Adaptado de FastAPI para Django REST Framework.
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

    @action(detail=False, methods=['post'], url_path='create')
    def create_report(self, request):
        """Deshabilitado: use /maintenance_scheduling/{id}/create-report/"""
        return Response(
            {
                "success": False,
                "message": "Use el endpoint /maintenance_scheduling/{id}/create-report/ para crear reportes."
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=False, methods=['get'], url_path='list')
    def list_reports(self, request):
        """
        Lista todos los reportes de mantenimiento.
        """
        
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 130  # maintenance_report.list
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar reportes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            queryset = MaintenanceReport.objects.select_related(
                'id_maintenance_scheduling',
                'id_maintenance_scheduling__id_machinery',
                'id_maintenance_scheduling__assigned_technician',
                'id_responsible_user'
            ).all().order_by('-registration_date')
            
            serializer = MaintenanceReportListSerializer(queryset, many=True)
            
            return Response(
                {
                    "success": True,
                    "message": "Lista de reportes de mantenimiento obtenida exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error listando reportes de mantenimiento: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al obtener la lista de reportes de mantenimiento",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='detail')
    def get_report_detail(self, request, pk=None):
        """
        Obtiene los detalles completos de un reporte de mantenimiento.
        """
        
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 131  # maintenance_report.detail
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para ver detalles de reportes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            report = MaintenanceReport.objects.select_related(
                'id_maintenance_scheduling',
                'id_maintenance_scheduling__id_machinery',
                'id_maintenance_scheduling__assigned_technician',
                'id_responsible_user'
            ).get(pk=pk)
            
            serializer = MaintenanceReportDetailSerializer(report)
            
            return Response(
                {
                    "success": True,
                    "message": "Detalles del reporte obtenidos exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except MaintenanceReport.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Reporte de mantenimiento no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles del reporte {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al obtener los detalles del reporte",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='download')
    def download_report(self, request, pk=None):
        """
        Descarga el PDF del reporte de mantenimiento.
        """
        # Verificar autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 128  # maintenance_report.download
        if not self.check_permission(request, permission_id):
            return Response({"message": "No tiene permisos para descargar reportes."}, status=status.HTTP_403_FORBIDDEN)

        try:
            report = MaintenanceReport.objects.select_related(
                'id_maintenance_scheduling',
                'id_maintenance_scheduling__id_machinery',
                'id_maintenance_scheduling__assigned_technician',
                'id_maintenance_scheduling__maintenance_type',
                'id_responsible_user'
            ).prefetch_related(
                'maintenance_relations__id_maintenance__maintenance_type',
                'spare_parts_used__spare_part_brand'
            ).get(pk=pk)

            # Preparar datos de tablas
            # Mantenimientos realizados
            maintenance_items = []

            # Obtener nombre del técnico desde servicio de usuarios (si es posible)
            tech_name = None
            try:
                assigned_id = getattr(getattr(report.id_maintenance_scheduling, 'assigned_technician', None), 'id_user', None)
                if assigned_id is not None:
                    base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
                    if base_url:
                        url = f"{base_url}/sigma/users/users/{assigned_id}"
                        headers = {}
                        # Pasar el mismo JWT recibido
                        auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or request.headers.get('Authorization')
                        if auth_header:
                            headers['Authorization'] = auth_header
                        resp = requests.get(url, headers=headers, timeout=10)
                        if resp.status_code == 200:
                            payload = resp.json()
                            # La API de usuarios responde { success, data: [...] } o { success, data: { ... } }
                            data_obj = payload.get('data', payload)
                            if isinstance(data_obj, list):
                                data_obj = data_obj[0] if data_obj else {}
                            # Nombre completo si existen campos
                            name = (data_obj or {}).get('name') or ''
                            fln = (data_obj or {}).get('first_last_name') or ''
                            sln = (data_obj or {}).get('second_last_name') or ''
                            full = ' '.join([p for p in [name, fln, sln] if p]).strip()
                            tech_name = full or str(assigned_id)
                        else:
                            tech_name = str(assigned_id)
            except Exception:
                tech_name = None
            for rel in getattr(report, 'maintenance_relations').all():
                m = rel.id_maintenance
                maintenance_items.append({
                    'name': getattr(m, 'name', 'N/D'),
                    'type': getattr(getattr(m, 'maintenance_type', None), 'name', 'N/D'),
                    'technician': tech_name or getattr(getattr(report.id_maintenance_scheduling, 'assigned_technician', None), 'id_user', 'N/D'),
                    'cost': getattr(rel, 'maintenance_cost', 'N/D'),
                })

            # Repuestos usados
            spare_parts = []
            for sp in getattr(report, 'spare_parts_used').all():
                total = float(sp.quantity_used) * float(sp.cost_at_time)
                spare_parts.append({
                    'name': getattr(sp, 'name', 'N/D'),
                    'brand': getattr(getattr(sp, 'spare_part_brand', None), 'name', 'N/D'),
                    'quantity': sp.quantity_used,
                    'unit_cost': sp.cost_at_time,
                    'total': total
                })

            pdf_bytes = build_maintenance_report_pdf(
                report=report,
                maintenance_items=maintenance_items,
                spare_parts=spare_parts,
                downloader_user_id=getattr(getattr(request, 'user', None), 'id_user', None),
                technician_name=tech_name
            )

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_{pk}.pdf"'
            return response

        except MaintenanceReport.DoesNotExist:
            return Response({"success": False, "message": "Reporte no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generando PDF del reporte {pk}: {str(e)}")
            return Response({"success": False, "message": "Error generando PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
