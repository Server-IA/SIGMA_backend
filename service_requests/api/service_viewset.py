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

# Serializers
from service_requests.serializers.service_serializers.service_create_serializer import ServiceCreateSerializer
from service_requests.serializers.service_serializers.service_list_serializer import ServiceListSerializer
from service_requests.serializers.service_serializers.service_update_serializer import ServiceUpdateSerializer

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

    def _get_service(self, pk):
        """
        Obtiene un servicio por su ID o lanza Http404.
        """
        try:
            return Service.objects.select_related(
                'service_type',
                'price_unit',
                'service_status',
                'id_responsible_user'
            ).get(pk=pk)
        except Service.DoesNotExist:
            raise Http404("Servicio no encontrado")
        except ValueError:
            raise Http404("ID de servicio inválido")

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

    @transaction.atomic
    @action(detail=True, methods=['patch'], url_path='update')
    def update_service(self, request, pk=None):
        """
        Actualiza un servicio existente.

        Requiere permiso: 141 (service.update)

        URL: PATCH /api/service-requests/services/{id}/update/

        Campos actualizables (todos opcionales):
        - service_name: Nombre del servicio (string, máximo 100 caracteres)
        - description: Descripción del servicio (string, máximo 500 caracteres)
        - service_type: ID del tipo de servicio (debe pertenecer a la categoría 14)
        - base_price: Precio base (decimal mayor a 0)
        - price_unit: ID de la unidad de medida (categoría 10)
        - applicable_tax: Indica si el impuesto es aplicable (entero)
        - tax_rate: Tasa de impuesto (decimal mayor a 0 si applicable_tax es True)
        - is_vat_exempt: Indica si está exento de IVA (booleano)

        Campos NO actualizables:
        - service_status: El estado del servicio no se puede modificar mediante este endpoint
        - id_responsible_user: El usuario responsable no se puede modificar

        Validaciones:
        - El nombre debe ser único (si se modifica)
        - El precio base debe ser mayor a 0
        - El tipo de servicio debe pertenecer a la categoría 14
        - La unidad de medida debe pertenecer a la categoría 10
        - Si applicable_tax es True, tax_rate es obligatoria

        Respuestas:
        - 200: Servicio actualizado exitosamente
        - 400: Error de validación
        - 401: Usuario no autenticado
        - 403: Sin permisos
        - 404: Servicio no encontrado
        - 500: Error del servidor
        """
        # 1. Verificar autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 2. Verificar permisos
        permission_id = 141  # service.update
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para actualizar servicios"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # 3. Obtener la instancia del servicio
            service = self._get_service(pk)

            # 4. Capturar snapshot antes de actualizar para auditoría
            before = service_snapshot(service)

            # 5. Validar y actualizar con el serializer
            serializer = ServiceUpdateSerializer(
                instance=service,
                data=request.data,
                partial=True,  # Permite actualización parcial
                context={'request': request}
            )

            if serializer.is_valid():
                # 6. Guardar los cambios
                updated_service = serializer.save()

                # 7. Registrar auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).update(
                        object_id=str(updated_service.id_service),
                        before=before,
                        after=service_snapshot(updated_service),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="requests",
                        submodule="service",
                    )
                except Exception as e:
                    logger.warning(
                        "El servicio de auditoría ha fallado en update_service: %s", str(e)
                    )

                # 8. Respuesta exitosa
                return Response({
                    'success': True,
                    'message': 'Servicio actualizado exitosamente',
                    'service_id': updated_service.id_service
                }, status=status.HTTP_200_OK)

            # Error de validación
            return Response({
                'success': False,
                'message': 'Error de validación',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Http404 as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error al actualizar servicio: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Error al procesar la solicitud',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        permission_id = 145
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
                if before_status_id == 1:
                    new_status = Statues.objects.get(pk=2)
                    new_status_id = 2
                    message = "Servicio inactivado exitosamente"
                else:
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
        Elimina un servicio.
        """
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 144  # service.delete
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para eliminar servicios."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            service = self._get_service(pk)
        except Http404:
            return Response(
                {"success": False, "message": "Servicio no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        before = service_snapshot(service)

        try:
            service.delete()

            # Auditoría
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                AuditClient(request).delete(
                    object_id=str(before.get("id_service") or service.id_service),
                    before=before,
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
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

        except IntegrityError as e:
            logger.error(f"Error de integridad al eliminar servicio: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "code": 409,
                "message": "No se puede eliminar el servicio porque tiene referencias asociadas.",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_409_CONFLICT)

        except Exception as e:
            logger.error(f"Error al eliminar el servicio: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "code": 500,
                "message": "Error al eliminar el servicio.",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)