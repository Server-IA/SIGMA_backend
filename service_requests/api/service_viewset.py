from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
import logging

# Serializers
from service_requests.serializers.service_serializers.service_create_serializer import ServiceCreateSerializer

# Models
from service_requests.models.services import Service

# Auditoría
from audit_sdk import AuditClient
from service_requests.utils.audit_helpers import get_actor_info, service_snapshot

logger = logging.getLogger(__name__)

class ServiceViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de servicios.
    """

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

    @action(detail=False, methods=['post'], url_path='create')
    def create_service(self, request):
        """
        Crea un nuevo servicio.
        
        Requiere permiso: 140 (service.create)
        
        Campos obligatorios:
        - service_name: Nombre del servicio (string, máximo 100 caracteres)
        - service_type: ID del tipo de servicio (debe pertenecer a la categoría 14)
        - base_price: Precio base (decimal mayor a 0)
        - price_unit: ID de la unidad de medida
        - applicable_tax: Indica si el impuesto es aplicable (entero)
        - responsible_user: ID del usuario responsable (se obtiene del token)
        
        Campos opcionales:
        - description: Descripción del servicio (string, máximo 500 caracteres)
        - tax_rate: Tasa de impuesto (decimal mayor a 0 si applicable_tax es True)
        - is_vat_exempt: Indica si está exento de IVA (booleano, opcional, por defecto False)
        """
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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
