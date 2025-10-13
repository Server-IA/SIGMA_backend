from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

# Serializers
from service_requests.serializers.service_serializers.service_create_serializer import ServiceCreateSerializer
from service_requests.serializers.service_serializers.service_list_serializer import ServiceListSerializer

# Models
from service_requests.models.services import Service

# Auditoría
from audit_sdk import AuditClient
from service_requests.utils.audit_helpers import get_actor_info, service_snapshot

logger = logging.getLogger(__name__)

class ServiceViewSet(viewsets.ViewSet):
    

    def check_permission(self, request, required_permission_id: int):
        
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

    def list(self, request):
        
        permission_id = 142
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para listar servicios."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            qs = Service.objects.select_related('service_type', 'price_unit', 'service_status').all()
            qs = qs.order_by('-modification_date')

            serializer = ServiceListSerializer(
                qs, many=True, context={
                    'request': request,
                }
            )

            return Response({
                "success": True,
                "data": serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("Error al listar servicios: %s", str(e), exc_info=True)
            return Response({
                "success": False,
                "message": "Error interno del servidor al listar los servicios",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='create')
    def create_service(self, request):        
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 140  # service.create

        # Verificar permiso
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear un servicio."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = ServiceCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                # Crear el servicio
                service = serializer.save()

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).create(
                        object_id=str(service.id_service),
                        after=service_snapshot(service),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="requests",
                        submodule="service",
                    )
                except Exception as e:
                    logger.warning(
                        "El servicio de auditoría ha fallado en create_service: %s", e
                    )

                return Response(
                    {
                        "success": True,
                        "message": "Servicio creado exitosamente",
                        "service_id": service.id_service
                    },
                    status=status.HTTP_201_CREATED
                )
            
            return Response(
                {
                    "success": False,
                    "message": "Error al crear el servicio",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error("Error al crear servicio: %s", str(e), exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor al crear el servicio",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        permission_id = 143
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para listar servicios."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            qs = Service.objects.select_related('service_type', 'price_unit', 'service_status').filter(service_status_id=1)
            qs = qs.order_by('-modification_date')

            serializer = ServiceListSerializer(
                qs, many=True, context={
                    'request': request,
                }
            )

            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error al listar servicios activos (permiso 143): %s", str(e), exc_info=True)
            return Response({
                "success": False,
                "message": "Error interno del servidor al listar los servicios activos",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)