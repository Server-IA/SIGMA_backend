from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_create_serializer import (
    MaintenanceSchedulingCreateSerializer,
)
from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_cancel_serializer import (
    MaintenanceSchedulingCancelSerializer,
)
from maintenance.models import MaintenanceScheduling, MaintenanceSchedulingCancellation

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

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """
        HU-PM-004: Cancelar mantenimiento programado.
        - Permiso requerido: ID 119 (maintenance_scheduling.delete)
        - Requiere motivo de cancelación.
        - Solo permite cancelar programaciones futuras y no canceladas previamente.
        """
        # Autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 119
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para cancelar mantenimientos programados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        scheduling = get_object_or_404(MaintenanceScheduling, pk=pk)

        # Impedir cancelar mantenimientos ya ejecutados/finalizados (fecha en pasado o igual a ahora)
        now = timezone.now()
        if scheduling.scheduled_at <= now:
            return Response(
                {
                    "success": False,
                    "message": "No es posible cancelar un mantenimiento ya ejecutado o finalizado.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Impedir cancelaciones repetidas
        if hasattr(scheduling, "cancellations") and scheduling.cancellations.exists():
            return Response(
                {
                    "success": False,
                    "message": "El mantenimiento programado ya fue cancelado previamente.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        ser = MaintenanceSchedulingCancelSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {"success": False, "message": "Error de validación", "details": ser.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = ser.validated_data["reason"].strip()

        try:
            with transaction.atomic():
                cancel_rec = MaintenanceSchedulingCancellation.objects.create(
                    id_maintenance_scheduling=scheduling,
                    reason=reason,
                    canceled_by=request.user,
                )
                # Tocar fecha de modificación para reflejar cambio
                scheduling.modification_date = now
                scheduling.save(update_fields=["modification_date"])

            return Response(
                {
                    "success": True,
                    "message": "Mantenimiento programado cancelado exitosamente.",
                    "data": {
                        "id_maintenance_scheduling": scheduling.id_maintenance_scheduling,
                        "canceled_at": cancel_rec.canceled_at,
                        "reason": cancel_rec.reason,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error cancelando mantenimiento programado: {str(e)}")
            return Response(
                {"success": False, "message": "Error al cancelar el mantenimiento programado.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
