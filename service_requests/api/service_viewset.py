from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
import logging
from django.db import transaction, IntegrityError
from django.http import Http404
from rest_framework import status
from service_requests.models.services import Service
from parameterization.models import Statues
from audit_sdk import AuditClient

# Serializers
from service_requests.serializers.service_serializers.service_create_serializer import ServiceCreateSerializer

# Models
from service_requests.models.services import Service

# Auditoría

from service_requests.utils.audit_helpers import get_actor_info, service_snapshot

logger = logging.getLogger(__name__)

class ServiceViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de servicios.
    """

    def _get_service(self, pk):
        """
        Retorna una instancia del servicio o lanza Http404 si no existe.
        """
        try:
            return Service.objects.get(id_service=pk)
        except Service.DoesNotExist:
            raise Http404

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

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        Activa/Inactiva un servicio (1 Activo, 2 Inactivo) mediante toggle.
        """
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 145  # Ajustar según matriz de permisos: services.toggle
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para activar/desactivar servicios."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            service = Service.objects.get(id_service=pk)
            
            try:
                from parameterization.models import Statues
                before_status_id = getattr(service, 'service_status_id', None)
                if before_status_id == 1:  # Activo a Inactivo
                    new_status = Statues.objects.get(pk=2)
                    new_status_id = 2
                    message = "Servicio inactivado exitosamente"
                else:  # Inactivo a Activo
                    new_status = Statues.objects.get(pk=1)
                    new_status_id = 1
                    message = "Servicio activado exitosamente"

                service.service_status = new_status
                service.save(update_fields=['service_status'])

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                    AuditClient(request).update(
                        object_id=str(service.id_service),
                        before={"service_status": before_status_id},
                        after={"service_status": new_status_id},
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="requests",
                        submodule="service",
                    )
                except Exception as e:
                    logger.warning("El servicio de auditoría ha fallado en toggle_status_service: %s", str(e))

                return Response({"success": True, "message": message}, status=status.HTTP_200_OK)

            except Statues.DoesNotExist:
                return Response(
                    {"success": False, "message": "Estado no válido."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Service.DoesNotExist:
            return Response(
                {"success": False, "message": "Servicio no encontrado."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al cambiar el estado del servicio: {str(e)}")
            return Response(
                {"success": False, "message": "Error al cambiar el estado del servicio.", "error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        Elimina un servicio si no tiene referencias. Si hay integridad referencial,
        realiza un soft delete (inactivación) y registra la auditoría.
        """
        # --- 1. Validar autenticación ---
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        # --- 2. Verificar permiso ---
        permission_id_delete = 144  # Ajustar según matriz de permisos: services.delete
        if not self.check_permission(request, permission_id_delete):
            return Response(
                {"success": False, "message": "No tiene permisos para eliminar servicios."},
                status=status.HTTP_403_FORBIDDEN
            )

        # --- 3. Obtener el servicio ---
        try:
            service = self._get_service(pk)
        except Http404:
            return Response({"success": False, "message": "Servicio no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # --- 4. Guardar snapshot antes de eliminar ---
        before = service_snapshot(service)

        # --- 5. Intentar eliminación dura ---
        try:
            service.delete()

            # --- 6. Registrar auditoría de eliminación definitiva ---
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                AuditClient(request).delete(
                    object_id=str(before.get("id_service") or service.id_service),
                    before=before,
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id_delete,
                    module="requests",
                    submodule="service",
                )
            except Exception as e:
                logger.warning("El servicio de auditoría ha fallado en delete_service: %s", e)

            return Response({
                "success": True,
                "code": 200,
                "message": "Servicio eliminado correctamente.",
                "data": None
            }, status=status.HTTP_200_OK)

        # --- 7. Manejar integridad referencial (soft delete) ---
        except IntegrityError:
            try:
                service.service_status = Statues.objects.get(pk=2)  # Estado inactivo
                service.save(update_fields=['service_status'])

                # Auditoría de inactivación lógica
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                    AuditClient(request).update(
                        object_id=str(before.get("id_service") or service.id_service),
                        before=before,
                        after=service_snapshot(service),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id_delete,
                        module="requests",
                        submodule="services",
                    )
                except Exception as e:
                    logger.warning("El servicio de auditoría ha fallado en soft_delete_service: %s", e)

                return Response({
                    "success": False,
                    "code": 409,
                    "message": "El servicio tiene referencias asociadas. Se ha inactivado lógicamente.",
                    "errors": {"detail": ["No se permite eliminación definitiva por integridad de datos."]}
                }, status=status.HTTP_409_CONFLICT)

            except Statues.DoesNotExist:
                return Response(
                    {"success": False, "message": "Estado inactivo no configurado."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as e:
                logger.error(f"Error al inactivar el servicio: {str(e)}")
                return Response(
                    {"success": False, "message": "Error al inactivar el servicio.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # --- 8. Otros errores ---
        except Exception as e:
            logger.error(f"Error al eliminar el servicio: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "message": "Error al eliminar el servicio.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )