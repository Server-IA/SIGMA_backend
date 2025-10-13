from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging
from audit_sdk import AuditClient
from django.db import transaction

from service_requests.models import ServiceRequest
from service_requests.serializers.service_request_serializers.pre_request_create_serializer import PreRequestCreateSerializer
from service_requests.utils.audit_helpers import get_actor_info, service_request_snapshot

logger = logging.getLogger(__name__)

class ServiceRequestViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de solicitudes de servicio.
    """
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

    @action(detail=False, methods=['post'])
    def create_pre_request(self, request):
        """
        Crea una nueva pre-solicitud de servicio.
        """
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 145
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear pre-solicitudes de servicio"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = PreRequestCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                with transaction.atomic():
                    service_request = serializer.save()

                    # Auditoría
                    try:
                        actor_id, actor_name, actor_role_name = get_actor_info(request.user)

                        AuditClient(request).create(
                            object_id=str(service_request.id_request),
                            after=service_request_snapshot(service_request),
                            actor_id=actor_id,
                            actor_name=actor_name,
                            actor_role=actor_role_name,
                            permission_id=permission_id,
                            module="requests",
                            submodule="requests",
                        )
                    except Exception as e:
                        logger.warning("El servicio de auditoría ha fallado en create_pre_request: %s", str(e))

                return Response({
                    'success': True,
                    'message': 'Pre-solicitud creada exitosamente',
                    'id_request': service_request.id_request
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Error en la validación de datos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error inesperado al crear pre-solicitud: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Ocurrió un error inesperado al procesar la solicitud',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
