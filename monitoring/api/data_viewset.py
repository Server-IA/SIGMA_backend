from monitoring.models.data import Data
from monitoring.serializers.historical_data_report_serializer import HistoricalDataReportSerializer
from monitoring.services.reporte_service import ReportService
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging
from audit_sdk import AuditClient
from django.db import transaction
from django.utils import timezone


logger = logging.getLogger(__name__)

class DataViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

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

    @action(detail=False, methods=['get'], url_path='generate-report')
    def generate_report(self, request):
        """Generar un reporte de datos históricos."""

        try:
            # 1. Verificar autenticación del usuario
            if not request.user.is_authenticated:
                return Response({
                    "success": False,
                    "message": "Usuario no autenticado"
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # 2. Validar permisos
            if not self.check_permission(request, 173):  # monitoring.download_historical_report
                return Response({
                    "success": False,
                    "message": "No tiene permiso para generar reportes"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 3. Validar parámetros de consulta
            serializer = HistoricalDataReportSerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Parámetros inválidos",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            report_format = validated_data.get('report_format', 'excel')
            request_id = validated_data.get('request_id', None)

            # 4. Construir queryset para el reporte
            queryset = self._build_historical_data_queryset(request_id=request_id)

            # 5. Verificar si hay datos para el reporte
            if not queryset.exists():
                return Response({
                    "success": False,
                    "message": "No hay datos disponibles para la solicitud seleccionada"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 6. Generar el reporte
            return ReportService.generate_report_response(
                queryset=queryset,
                format_type=report_format
            )


        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Error interno generando el reporte"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _build_historical_data_queryset(self, request_id=None):
        """Construir el queryset para datos históricos basado en filtros."""

        queryset = Data.objects.all()

        if request_id is not None:
            queryset = queryset.filter(request_id=request_id)

        return queryset