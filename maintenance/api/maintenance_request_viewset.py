from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

from maintenance.serializers.maintenance_request_serializers.maintenance_request_create_serializer import (
    MaintenanceRequestCreateSerializer,
)

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

        permission_id = 116  # Ajustar según el ID real de "crear solicitud de mantenimiento"
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para registrar solicitudes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            serializer = MaintenanceRequestCreateSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                instance = serializer.save()
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
                status=status.HTTP_400_BAD_REQUEST,
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
