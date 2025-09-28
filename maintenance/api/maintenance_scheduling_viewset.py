from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging
from django.shortcuts import get_object_or_404

from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_create_serializer import (
    MaintenanceSchedulingCreateSerializer,
)
from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_update_serializer import (
    MaintenanceSchedulingUpdateSerializer,
)
from maintenance.models import MaintenanceScheduling
from core.services.notification_service import (
    notify_maintenance_scheduling_update,
    MaintenanceSchedulingNotificationContext,
)

logger = logging.getLogger(__name__)


class MaintenanceSchedulingViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar la programación de mantenimientos sin solicitud previa.
    """

    def check_permission(self, request, required_permission_id: int):
        payload = getattr(request, "auth", None) or {}
        user_roles = payload.get("rol") or payload.get("roles") or []

        permisos_usuario = []
        for rol in user_roles:
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))

        return required_permission_id in permisos_usuario

    @action(detail=False, methods=["post"], url_path="create")
    def create_scheduling(self, request):
        """
        Crea un mantenimiento programado. Requiere permiso ID 117.
        Campos esperados:
          - id_machinery
          - scheduled_at
          - details (<= 350 chars)
          - assigned_technician
          - maintenance_type (categoría id=12)
          - id_responsible_user
        """
        # Autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 117
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para programar mantenimientos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            serializer = MaintenanceSchedulingCreateSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                instance = serializer.save()
                return Response(
                    {
                        "success": True,
                        "message": "Mantenimiento programado creado exitosamente",
                        "data": {"id_maintenance_scheduling": instance.id_maintenance_scheduling},
                    },
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error creando mantenimiento programado: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al crear el mantenimiento programado",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _is_executed(self, scheduling: MaintenanceScheduling) -> bool:
        """
        Dado que no hay flag explícito en el modelo, inferimos 'ejecutado' por el estado
        de la solicitud asociada (si existe) usando el nombre del estado.
        """
        req = getattr(scheduling, "id_maintenance_request", None)
        status_name = (getattr(getattr(req, "request_status", None), "name", "") or "").lower()
        return any(k in status_name for k in ["ejecut", "finaliz", "complet", "cerrad"])

    @action(detail=True, methods=["put", "patch"], url_path="update")
    def update_scheduling(self, request, pk=None):
        """
        Actualiza un mantenimiento programado. Requiere permiso ID 119.
        Valida:
         - no permitir si ya fue ejecutado
         - fecha/hora en futuro
         - disponibilidad de técnico
         - tipo de mantenimiento en categoría id=12
        """
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 119
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar la programación de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        scheduling = get_object_or_404(MaintenanceScheduling, pk=pk)

        # Regla HU: No se permite actualizar si ya fue ejecutado
        if self._is_executed(scheduling):
            return Response(
                {
                    "success": False,
                    "message": "No es posible actualizar: el mantenimiento ya fue ejecutado.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        previous_tech_id = getattr(scheduling.assigned_technician, "id_user", None) or getattr(
            scheduling.assigned_technician, "id", None
        )

        serializer = MaintenanceSchedulingUpdateSerializer(
            scheduling, data=request.data, partial=True, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                {"success": False, "message": "Error de validación", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = serializer.save()

        # Notificación: técnico actual y nuevo (si hubo cambio)
        new_tech_id = getattr(instance.assigned_technician, "id_user", None) or getattr(
            instance.assigned_technician, "id", None
        )
        try:
            notify_maintenance_scheduling_update(
                MaintenanceSchedulingNotificationContext(
                    scheduling_id=instance.id_maintenance_scheduling,
                    machinery_id=instance.id_machinery_id,
                    scheduled_at=str(instance.scheduled_at),
                    previous_technician_id=previous_tech_id,
                    new_technician_id=new_tech_id,
                )
            )
        except Exception as e:
            # No bloquear el flujo por falla de notificación
            logger.warning(f"No se pudo enviar notificación de actualización: {e}")

        # Datos requeridos por HU para mostrar en confirmación
        machinery = instance.id_machinery
        request_date = getattr(getattr(instance, "id_maintenance_request", None), "detected_at", None)

        return Response(
            {
                "success": True,
                "message": "Programación de mantenimiento actualizada correctamente.",
                "data": {
                    "id_maintenance_scheduling": instance.id_maintenance_scheduling,
                    "machinery_serial_number": getattr(machinery, "serial_number", None),
                    "machinery_name": getattr(machinery, "machinery_name", None),
                    "request_date": request_date,
                    "scheduled_at": instance.scheduled_at,
                    "assigned_technician": new_tech_id,
                    "maintenance_type": instance.maintenance_type_id,
                    "details": instance.details,
                },
            },
            status=status.HTTP_200_OK,
        )
