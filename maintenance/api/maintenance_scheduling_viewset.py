from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging
from django.shortcuts import get_object_or_404

from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_create_serializer import (MaintenanceSchedulingCreateSerializer)
from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_cancel_serializer import (MaintenanceSchedulingCancelSerializer)
from maintenance.models import MaintenanceScheduling
from maintenance.models.maintenance_scheduling import MaintenanceScheduling
from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_List_serializer import (
    MaintenanceSchedulingListSerializer,
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

        permission_id = 1
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para programar mantenimientos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Pasamos el request al contexto del serializador para que pueda acceder al usuario autenticado
            serializer = MaintenanceSchedulingCreateSerializer(
                data=request.data, 
                context={"request": request}
            )
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
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    def cancel_scheduling(self, request, pk=None):
        """
        HU-PM-004: Cancelar mantenimiento programado.
        - Permiso requerido: 121 ('maintenance_scheduling.canceled').
        - Justificación obligatoria.
        - No permite cancelar si ya está cancelado (estado=14) o finalizado (estado=15).
        """
        # Autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 121
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para cancelar mantenimientos programados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        scheduling = get_object_or_404(
            MaintenanceScheduling.objects.select_related("maintenance_scheduling_status"),
            pk=pk
        )

        try:
            serializer = MaintenanceSchedulingCancelSerializer(
                data=request.data, context={"request": request, "instance": scheduling}
            )
            if serializer.is_valid():
                scheduling = serializer.save()
                return Response(
                    {
                        "success": True,
                        "message": "Mantenimiento programado cancelado exitosamente.",
                        "data": {"id_maintenance_scheduling": scheduling.id_maintenance_scheduling},
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": serializer.errors,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Exception as e:
            logger.error(f"Error cancelando mantenimiento programado {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al cancelar el mantenimiento programado",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    @action(detail=False, methods=["get"], url_path="list")
    def list_schedulings(self, request):
        """
        HU-PM-002: Listar mantenimientos programados.
        - Permiso requerido: 118 (consulta).
        """
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 125
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para consultar mantenimientos programados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        schedulings = MaintenanceScheduling.objects.select_related(
            "id_machinery", "assigned_technician", "maintenance_scheduling_status"
        ).all()

        if not schedulings:
            return Response(
                {"success": False, "message": "No se encontraron resultados."},
                status=status.HTTP_200_OK,
            )

        serializer = MaintenanceSchedulingListSerializer(schedulings, many=True)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )