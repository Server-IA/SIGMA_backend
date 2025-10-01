from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

from maintenance.models import MaintenanceScheduling, MaintenanceReport
from parameterization.models import Statues
from maintenance.serializers.maintenance_report_serializers import MaintenanceReportCreateSerializer

logger = logging.getLogger(__name__)


class MaintenanceSchedulingReportViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar la creación de reportes desde mantenimientos programados.
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

    @action(detail=True, methods=['post'], url_path='create-report')
    def create_maintenance_report(self, request, pk=None):
        """
        Crea un reporte de mantenimiento para un mantenimiento programado específico.
        
        Este endpoint cumple con el criterio de aceptación #1 de HU-PM-005:
        "El sistema debe permitir registrar reporte de mantenimientos programados 
        desde el listado de mantenimientos programados, a través de un botón de 'Reporte'."
        
        Campos requeridos:
        - title: Título del reporte
        - description: Descripción del mantenimiento (máximo 600 caracteres)
        - time_invested_hours: Horas invertidas
        - time_invested_minutes: Minutos invertidos
        - maintenance_items: Lista de IDs de mantenimientos realizados
        - spare_parts: Lista de repuestos utilizados
        
        Campos opcionales:
        - recommendations: Recomendaciones
        """
        
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 127  # maintenance_scheduling.create_report
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear reportes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Verificar que el mantenimiento programado existe
            try:
                scheduling = MaintenanceScheduling.objects.select_related(
                    'maintenance_scheduling_status'
                ).get(pk=pk)
            except MaintenanceScheduling.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Mantenimiento programado no encontrado"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validar que el mantenimiento esté en estado 13 (pendiente de reporte)
            if scheduling.maintenance_scheduling_status.id_statues != 13:
                return Response(
                    {
                        "success": False,
                        "message": "Solo se pueden crear reportes para mantenimientos en estado 13 (pendiente de reporte)",
                        "details": f"Estado actual: {scheduling.maintenance_scheduling_status.id_statues}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que la maquinaria esté en estado 6 antes de generar el reporte
            machinery = scheduling.id_machinery
            try:
                current_status_id = machinery.machinery_operational_status.id_statues
            except Exception:
                current_status_id = None
            if current_status_id != 6:
                return Response(
                    {
                        "success": False,
                        "message": "La maquinaria debe estar en estado 6 para poder generar el reporte.",
                        "details": f"Estado actual de la maquinaria: {current_status_id}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que no exista ya un reporte para este mantenimiento
            existing_report = MaintenanceReport.objects.filter(
                id_maintenance_scheduling=scheduling
            ).first()
            
            if existing_report:
                return Response(
                    {
                        "success": False,
                        "message": "Ya existe un reporte para este mantenimiento programado",
                        "details": f"Reporte ID: {existing_report.id_maintenance_report}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Agregar el ID del mantenimiento programado. El usuario responsable viene en el body como 'responsible_user'
            request.data['id_maintenance_scheduling'] = scheduling.id_maintenance_scheduling
            
            serializer = MaintenanceReportCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                instance = serializer.save()

                # Cambiar estado de la programación a 15 (ejecutado) al registrar el reporte
                try:
                    executed_status = Statues.objects.get(pk=15)
                    scheduling.maintenance_scheduling_status = executed_status
                    scheduling.save(update_fields=["maintenance_scheduling_status"]) 
                except Statues.DoesNotExist:
                    logger.error("Estado 15 (ejecutado) no encontrado en Statues")
                
                # Cambiar estado de la maquinaria a Activo (id=4)
                try:
                    active_status = Statues.objects.get(pk=4)
                    machinery.machinery_operational_status = active_status
                    machinery.save(update_fields=["machinery_operational_status"]) 
                except Statues.DoesNotExist:
                    logger.error("Estado 4 (Activo) no encontrado en Statues")
                
                # TODO: Implementar notificaciones según criterio de aceptación #8
                # self._notify_report_creation(instance)
                
                return Response(
                    {
                        "success": True,
                        "message": "Reporte de mantenimiento creado exitosamente",
                        "data": {
                            "id_maintenance_report": instance.id_maintenance_report,
                            "title": instance.title,
                            "total_cost": instance.total_cost,
                            "machinery_serial": scheduling.id_machinery.serial_number,
                            "machinery_name": scheduling.id_machinery.machinery_name,
                            "assigned_technician_id": scheduling.assigned_technician.id_user
                        }
                    },
                    status=status.HTTP_201_CREATED
                )
                
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error creando reporte para mantenimiento {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al crear el reporte de mantenimiento",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _notify_report_creation(self, report):
        """
        Notifica a los usuarios con permisos sobre la creación del reporte.
        Implementa el criterio de aceptación #8 de HU-PM-005.
        """
        # TODO: Implementar sistema de notificaciones
        # - Buscar usuarios con permisos de notificación de reporte
        # - Enviar notificación sobre el nuevo reporte
        pass
