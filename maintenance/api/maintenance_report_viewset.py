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

        # Permisos deshabilitados temporalmente
        # permission_id = 130  # maintenance_report.list
        # if not self.check_permission(request, permission_id):
        #     return Response(
        #         {"message": "No tiene permisos para listar reportes de mantenimiento."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

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

        # Permisos deshabilitados temporalmente
        # permission_id = 131  # maintenance_report.detail
        # if not self.check_permission(request, permission_id):
        #     return Response(
        #         {"message": "No tiene permisos para ver detalles de reportes de mantenimiento."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

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
