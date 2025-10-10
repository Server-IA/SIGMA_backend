from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
# Prefer relative imports within the app package
from service_requests.models.customer import Customer
from service_requests.serializers.customer_serializers.customer_create_serializer import CustomerCreateSerializer
from service_requests.serializers.customer_serializers.customer_detail_serializer import CustomerDetailSerializer
from service_requests.utils.audit_helpers import get_actor_info, customer_snapshot
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging
from audit_sdk import AuditClient
from django.db import transaction, IntegrityError
from django.http import Http404
from parameterization.models import Statues

logger = logging.getLogger(__name__)

class CustomerViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de clientes.
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

    def _get_customer(self, pk: int) -> Customer:
        return get_object_or_404(Customer, id_customer=pk)

    @action(detail=False, methods=['post'])
    def create_customer(self, request):
        """
        Crea un nuevo cliente.
        """
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 133
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear clientes"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = CustomerCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                customer = serializer.save()

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)

                    AuditClient(request).create(
                        object_id=str(customer.id_customer),
                        after=customer_snapshot(customer),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="requests",
                        submodule="customers",
                    )
                except Exception as e:
                    logger.warning("El servicio de auditoría ha fallado en create_customer: %s", str(e))

                return Response({
                    'success': True,
                    'message': 'Cliente creado exitosamente',
                    'id_customer': customer.id_customer
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Error de validación',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error al crear cliente: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al procesar la solicitud',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='detail')
    def retrieve_with_details(self, request, pk=None):
        """
        Endpoint para consultar el detalle de un cliente (HU-CLI-003).
        Incluye únicamente información personal, contacto y estado del cliente.
        """
        # 1. Verificar permisos (ID ajustable según tu matriz de permisos)
        permission_id = 134
        if not hasattr(self, 'check_permission') or not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para ver el detalle del cliente."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # 2. Obtener el cliente de la BD con select_related para FK
            customer = Customer.objects.select_related(
                'type_document_id', 'person_type', 'customer_statues'
            ).get(id_customer=pk)
        except Customer.DoesNotExist:
            return Response(
                {"success": False, "message": "Cliente no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al consultar cliente: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al procesar la solicitud',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3. Serializar y responder solo con los datos del cliente
        customer_data = CustomerDetailSerializer(customer, context={'request': request}).data

        return Response({
            "success": True,
            "message": "Detalle del cliente obtenido exitosamente",
            "data": customer_data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        Activa/Inactiva un cliente (1 Activo, 2 Inactivo) mediante toggle.
        """
        if not request.user.is_authenticated:
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 139  # Ajustar según matriz de permisos: customers.toggle
        if not self.check_permission(request, permission_id):
            return Response({"message": "No tiene permisos para activar/desactivar clientes."}, status=status.HTTP_403_FORBIDDEN)

        try:
            customer = self._get_customer(pk)

            try:
                before_status_id = getattr(customer, 'customer_statues_id', None)
                if before_status_id == 1:
                    new_status = Statues.objects.get(pk=2)
                    new_status_id = 2
                    message = "Cliente inactivado exitosamente"
                else:
                    new_status = Statues.objects.get(pk=1)
                    new_status_id = 1
                    message = "Cliente activado exitosamente"

                customer.customer_statues = new_status
                customer.save(update_fields=['customer_statues'])

                # Auditoría (solo id de estado)
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                    AuditClient(request).update(
                        object_id=str(customer.id_customer),
                        before={"customer_statues": before_status_id},
                        after={"customer_statues": new_status_id},
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="requests",
                        submodule="customers",
                    )
                except Exception as e:
                    logger.warning("El servicio de auditoría ha fallado en toggle_status_customer: %s", e)

                return Response({"success": True, "message": message}, status=status.HTTP_200_OK)

            except Statues.DoesNotExist:
                return Response({"success": False, "message": "Estado no válido."}, status=status.HTTP_400_BAD_REQUEST)

        except Http404:
            return Response({"success": False, "message": "Cliente no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"success": False, "message": "Error al cambiar el estado.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        Elimina un cliente si no tiene referencias. Si hay integridad referencial, realiza soft delete (inactivar) y registra auditoría.
        """
        if not request.user.is_authenticated:
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id_delete = 138  # Ajustar según matriz de permisos: customers.delete
        if not self.check_permission(request, permission_id_delete):
            return Response({"message": "No tiene permisos para eliminar clientes."}, status=status.HTTP_403_FORBIDDEN)

        try:
            customer = self._get_customer(pk)
        except Http404:
            return Response({"success": False, "message": "Cliente no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Snapshot antes de eliminar (igual que maintenance)
        before = customer_snapshot(customer)

        try:
            # Intento de eliminación dura
            customer.delete()

            # Auditoría - eliminación definitiva
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                AuditClient(request).delete(
                    object_id=str(before.get("id_customer") or customer.id_customer),
                    before=before,
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id_delete,
                    module="requests",
                    submodule="customers",
                )
            except Exception as e:
                logger.warning("El servicio de auditoría ha fallado en delete_customer: %s", e)

            return Response({
                "success": True,
                "code": 200,
                "message": "Cliente eliminado correctamente.",
                "data": None
            }, status=status.HTTP_200_OK)

        except IntegrityError:
            # Soft delete: inactivar por referencias existentes
            try:
                customer.customer_statues = Statues.objects.get(pk=2)
                customer.save(update_fields=['customer_statues'])

                # Intento de inactivar usuario asociado en microservicio de usuarios (placeholder)
                if getattr(customer, 'id_user_id', None):
                    # No hay campo de estado en users.User en este servicio. Aquí se podría llamar al microservicio externo.
                    logger.info("Cliente %s con usuario asociado %s: marcar como inactivo en microservicio de usuarios (pendiente de implementación)", customer.id_customer, customer.id_user_id)

                # Auditoría - inactivación lógica
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                    AuditClient(request).update(
                        object_id=str(after.get("id_customer") or customer.id_customer),
                        before=before,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id_delete,
                        module="requests",
                        submodule="customers",
                    )
                except Exception as e:
                    logger.warning("El servicio de auditoría ha fallado en soft_delete_customer: %s", e)

                return Response({
                    "success": False,
                    "code": 409,
                    "message": "El cliente tiene historial asociado. Se ha inactivado lógicamente.",
                    "errors": {"detail": ["No se permite eliminación definitiva por integridad de datos."]}
                }, status=status.HTTP_409_CONFLICT)

            except Statues.DoesNotExist:
                return Response({"success": False, "message": "Estado inactivo no configurado."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                return Response({"success": False, "message": "Error al inactivar el cliente.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"success": False, "message": "Error al eliminar el cliente.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)