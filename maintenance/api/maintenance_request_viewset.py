from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

from maintenance.serializers.maintenance_request_serializers.maintenance_request_create_serializer import (
    MaintenanceRequestCreateSerializer,
)
from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_from_request_create_serializer import (
    MaintenanceSchedulingFromRequestCreateSerializer,
)

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info
from maintenance.utils.audit_helpers import maintenance_request_snapshot, maintenance_scheduling_snapshot

logger = logging.getLogger(__name__)


class MaintenanceRequestViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar la creación de solicitudes de mantenimiento manuales.
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
    def create_request(self, request):
        """
        Crea una solicitud de mantenimiento manual.
        Requiere permiso ID 116 (ajustar si es diferente en tu parametrización de permisos).
        """
        # Autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 119
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para registrar solicitudes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            serializer = MaintenanceRequestCreateSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                instance = serializer.save()

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).create(
                        object_id=str(getattr(instance, "id_maintenance_request", "")),
                        after=maintenance_request_snapshot(instance),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="maintenance_request",
                    )
                except Exception as e:
                    logging.warning("El servicio de auditoría ha fallado en create_maintenance_request: %s", e)


                return Response(
                    {
                        "success": True,
                        "message": "Solicitud de mantenimiento registrada exitosamente",
                        "data": {"id_maintenance_request": instance.id_maintenance_request},
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
            logger.error(f"Error creando solicitud de mantenimiento: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al crear la solicitud de mantenimiento",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="schedule")
    def schedule_from_request(self, request, pk=None):
        """
        Programa un mantenimiento a partir de una solicitud existente (pk).
        Requiere permiso ID 117.
        """
        # Autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 120
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para programar mantenimientos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Inyectar el ID de la solicitud desde la URL en el payload del serializer
            data = request.data.copy()
            data["id_maintenance_request"] = pk

            serializer = MaintenanceSchedulingFromRequestCreateSerializer(
                data=data,
                context={"request": request},
            )

            if serializer.is_valid():
                scheduling = serializer.save()
                
                # Auditoría 
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).create(
                        object_id=str(getattr(scheduling, "id_maintenance_scheduling", "")),
                        after=maintenance_scheduling_snapshot(scheduling),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="maintenance_request_scheduled",
                    )
                except Exception as e:
                    logging.warning("El servicio de auditoría ha fallado en create_maintenance_scheduling_from_request: %s", e)


                return Response(
                    {
                        "success": True,
                        "message": "Mantenimiento programado exitosamente desde la solicitud",
                        "data": {
                            "id_maintenance_scheduling": scheduling.id_maintenance_scheduling,
                            "id_maintenance_request": pk,
                        },
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
            logger.error(f"Error programando mantenimiento desde solicitud {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al programar el mantenimiento",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
