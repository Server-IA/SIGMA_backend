from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_create_serializer import (
    MaintenanceSchedulingCreateSerializer,
)

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info
from maintenance.utils.audit_helpers import maintenance_scheduling_snapshot

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
            # Pasamos el request al contexto del serializador para que pueda acceder al usuario autenticado
            serializer = MaintenanceSchedulingCreateSerializer(
                data=request.data, 
                context={"request": request}
            )
            if serializer.is_valid():
                instance = serializer.save()

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).create(
                        object_id=str(getattr(instance, "id_maintenance_scheduling", "")),
                        after=maintenance_scheduling_snapshot(instance),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="maintenance_scheduling",
                    )
                except Exception as e:
                    logging.warning("El servicio de auditoría ha fallado en create_maintenance_scheduling: %s", e)

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
