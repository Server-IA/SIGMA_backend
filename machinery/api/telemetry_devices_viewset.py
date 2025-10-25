from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.machinery import Machinery
from machinery.models.telemetry_device_parameter import TelemetryDeviceParameter
from machinery.serializers.telemetry_devices_serializers.telemetry_devices_list_serializer import TelemetryDevicesListSerializer
from machinery.serializers.telemetry_devices_serializers.telemetry_devices_create_serializer import TelemetryDevicesCreateSerializer
from machinery.serializers.telemetry_devices_serializers.telemetry_devices_detailed_serializer import TelemetryDevicesDetailedSerializer
from machinery.utils.audit_helpers import telemetry_devices_snapshot, telemetry_device_parameter_snapshot, get_actor_info, telemetry_device_snapshot_toggle
from audit_sdk import AuditClient
import logging


from django.db import transaction
from django.shortcuts import get_object_or_404
from parameterization.models.statues import Statues
import logging
from django.db import IntegrityError
from django.http import Http404
from audit_sdk import AuditClient
logger = logging.getLogger(__name__)

class TelemetryDevicesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo TelemetryDevices.
    """

    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
        Adaptado de FastAPI para Django REST Framework.
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

    queryset = TelemetryDevices.objects.all()
    
    def get_serializer_class(self):
        """
        Retorna el serializador adecuado según la acción.
        """
        if self.action == 'create':
            return TelemetryDevicesCreateSerializer
        elif self.action == 'retrieve':
            from machinery.serializers.telemetry_devices_serializers.telemetry_devices_retrieve_serializer import TelemetryDevicesRetrieveSerializer
            return TelemetryDevicesRetrieveSerializer
        elif self.action == 'update_device':
            from machinery.serializers.telemetry_devices_serializers.telemetry_devices_update_serializer import TelemetryDevicesUpdateSerializer
            return TelemetryDevicesUpdateSerializer
        elif self.action == 'list':
            return TelemetryDevicesDetailedSerializer
        elif self.action == 'active':
            return TelemetryDevicesListSerializer
        return TelemetryDevicesListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # If the request is for active devices, only return active devices (status ID 1)
        if self.action == 'active':
            return queryset.filter(id_statues=1).order_by('name')
            
        # For list view, return all devices (no filtering)
        # Only exclude devices with null id_device to avoid serialization errors
        return queryset.exclude(
            id_device__isnull=True
        ).order_by('name')

    def retrieve(self, request, *args, **kwargs):
        """
        Obtiene información detallada de un dispositivo de telemetría por id_device.
        Requiere permiso 169 (telemetry_device.retrieve)
        """
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permiso 169 (telemetry_device.retrieve)
        permission_id = 169
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para obtener información del dispositivo de telemetría."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Buscar dispositivo por id_device en lugar del pk con prefetch para optimización
            id_device = kwargs.get('pk')
            device = get_object_or_404(
                TelemetryDevices.objects.prefetch_related('telemetrydeviceparameter_set__parameter'),
                id_device=id_device
            )

            serializer = self.get_serializer(device)
            return Response({
                'success': True,
                'message': 'Dispositivo encontrado exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Http404:
            return Response({
                'success': False,
                'message': 'Dispositivo no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error al obtener el dispositivo de telemetría: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al obtener el dispositivo',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)    

    def update(self, request, *args, **kwargs):
        
        """
        Actualiza un dispositivo de telemetría existente.
        Requiere permiso 114 (telemetry_device.update)
        """
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 114  # telemetry_device.update
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para actualizar dispositivos de telemetría."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener la instancia del dispositivo
            instance = self.get_object()
            
            # Tomar snapshot para auditoría
            before = telemetry_devices_snapshot(instance)
            
            # Obtener parámetros actuales para el snapshot
            current_params = list(instance.telemetrydeviceparameter_set.values_list('parameter_id', flat=True))
            
            # Validar y actualizar
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            # Realizar la actualización
            updated_device = serializer.save()
            
            # Obtener parámetros después de la actualización
            updated_params = list(updated_device.telemetrydeviceparameter_set.values_list('parameter_id', flat=True))
            
            # Registrar auditoría
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                
                # Preparar los datos para la auditoría
                after = telemetry_devices_snapshot(updated_device)
                
                # Si hay cambios en los parámetros, incluirlos en el after
                if set(current_params) != set(updated_params):
                    after["parameters"] = updated_params
                    before["parameters"] = current_params
                
                # Registrar una sola entrada de auditoría que incluya tanto el dispositivo como los parámetros
                AuditClient(request).update(
                    object_id=str(updated_device.id_device),
                    before=before,
                    after=after,
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="monitoring",
                    submodule="telemetry_devices",
                )
                    
            except Exception as e:
                logger.warning("El servicio de auditoría ha fallado en update: %s", str(e))
            
            # Obtener los datos actualizados para la respuesta
            from machinery.serializers.telemetry_devices_serializers.telemetry_devices_detailed_serializer import TelemetryDevicesDetailedSerializer
            device_data = TelemetryDevicesDetailedSerializer(updated_device, context={'request': request}).data
            
            return Response({
                'success': True,
                'message': 'Dispositivo actualizado exitosamente',
                'data': device_data
            }, status=status.HTTP_200_OK)
            
        except Http404:
            return Response({
                'success': False,
                'message': 'Dispositivo no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Error al actualizar el dispositivo de telemetría: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error al actualizar el dispositivo',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Lista todos los dispositivos de telemetría activos.
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 111  # telemetry_device.list_active

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar dispositivos de telemetría activos."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            queryset = self.get_queryset().filter(id_statues_id=1)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request, *args, **kwargs):
        """
        Lista todos los dispositivos de telemetría con información detallada.
        """
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 112  # telemetry_device.list

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar dispositivos de telemetría."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo dispositivo de telemetría con parámetros asociados.
        Requiere permiso 113 y registra auditoría.
        """
        # Verificar autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permiso 113 (telemetry_device.create)
        permission_id = 113
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear dispositivos de telemetría."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Usar el serializer personalizado
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        telemetry_device = serializer.save()

        # Auditoría
        try:
            actor_id, actor_name, actor_role_name = get_actor_info(request.user)

            # Crear snapshot del dispositivo principal
            main_snapshot = telemetry_devices_snapshot(telemetry_device)

            # Crear snapshots de parámetros asociados
            related_snapshots = []
            for param in telemetry_device.telemetrydeviceparameter_set.all():
                related_snapshots.append(telemetry_device_parameter_snapshot(param))

            # Combinar snapshots
            combined_after = {**main_snapshot}
            if related_snapshots:
                combined_after['parameters'] = related_snapshots

            AuditClient(request).create(
                object_id=str(telemetry_device.id_device),
                after=combined_after,
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role_name,
                permission_id=permission_id,
                module="monitoring",
                submodule="telemetry_devices",
            )
        except Exception as e:
            logger.warning("El servicio de auditoría ha fallado en create: %s", str(e))

        # Retornar respuesta
        return Response(
            {"message": "Dispositivo creado exitosamente", "id": telemetry_device.id_device},
            status=status.HTTP_201_CREATED
        )

    def _get_status_by_name(self, name: str):

        try:
            return Statues.objects.filter(name__iexact=name).first()
        except Exception:
            return None

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):

        # Autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response({"success": False, "message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 115
        if not self.check_permission(request, permission_id):
            return Response({"success": False, "message": "No tiene permisos para activar/desactivar dispositivos."}, status=status.HTTP_403_FORBIDDEN)

        try:
            device = TelemetryDevices.objects.get(pk=pk)
        except TelemetryDevices.DoesNotExist:
            return Response({"success": False, "message": "Dispositivo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            before_status_id = getattr(device, 'id_statues_id', None)
            before = telemetry_device_snapshot_toggle(device)
            if before_status_id == 1:
                new_status = Statues.objects.get(pk=2)
                new_status_id = 2
                message = "Dispositivo inactivado exitosamente"
            else:
                new_status = Statues.objects.get(pk=1)
                new_status_id = 1
                message = "Dispositivo activado exitosamente"

            with transaction.atomic():
                device.id_statues = new_status
                device.save(update_fields=['id_statues', 'modification_date'])

                logging.info(
                    "audit: telemetry_device.toggle_status",
                    extra={
                        "action": "toggle_status",
                        "before_status_id": before_status_id,
                        "after_status_id": new_status_id,
                        "id_device": device.id_device,
                        "name": device.name,
                        "user_id": getattr(request.user, 'id', None),
                    }
                )

                # Auditoría formal
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                    AuditClient(request).update(
                        object_id=str(device.id_device),
                        before=before,
                        after=telemetry_device_snapshot_toggle(device),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="monitoring",
                        submodule="telemetry_devices",
                    )
                except Exception as e:
                    logging.warning("El servicio de auditoría ha fallado en toggle_status: %s", str(e))

            return Response({"success": True, "message": message}, status=status.HTTP_200_OK)

        except Statues.DoesNotExist:
            return Response({"success": False, "message": "Estado no válido."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error("Error al cambiar el estado del dispositivo: %s", str(e))
            return Response({"success": False, "message": "Error al cambiar el estado del dispositivo.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):

        # Autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response({"success": False, "message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        # Permiso alineado a servicio: 162
        permission_id = 162
        if not self.check_permission(request, permission_id):
            return Response({"success": False, "message": "No tiene permisos para eliminar dispositivos de telemetría."}, status=status.HTTP_403_FORBIDDEN)

        # Obtener dispositivo o 404
        try:
            device = TelemetryDevices.objects.get(pk=pk)
        except TelemetryDevices.DoesNotExist:
            return Response({"success": False, "message": "Dispositivo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Eliminación física (sin soft delete)
        try:
            with transaction.atomic():
                # Obtener parámetros asociados antes de eliminar
                associated_parameters = device.telemetrydeviceparameter_set.all()

                # Eliminar parámetros intermedios primero
                parameters_count = associated_parameters.count()
                associated_parameters.delete()

                # Crear snapshot del dispositivo antes de eliminar
                before = telemetry_devices_snapshot(device)

                # Eliminar el dispositivo
                device.delete()

                logging.info(
                    "audit: telemetry_device.hard_delete",
                    extra={
                        "action": "hard_delete",
                        "id_device": before.get("id_device"),
                        "name": before.get("name"),
                        "parameters_deleted": parameters_count,
                        "user_id": getattr(request.user, 'id', None),
                    }
                )

                # Auditoría formal (delete)
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                    AuditClient(request).delete(
                        object_id=str(before.get("id_device")),
                        before=before,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="monitoring",
                        submodule="telemetry_devices",
                    )
                except Exception as e:
                    logging.warning("El servicio de auditoría ha fallado en destroy (hard_delete): %s", str(e))

            return Response({
                "success": True,
                "code": 200,
                "message": f"Dispositivo y sus {parameters_count} parámetros asociados eliminados correctamente.",
                "data": None
            }, status=status.HTTP_200_OK)
        except IntegrityError as e:
            logging.error("Error de integridad al eliminar dispositivo: %s", str(e), exc_info=True)
            return Response({
                "success": False,
                "code": 409,
                "message": "No se puede eliminar el dispositivo porque tiene referencias asociadas.",
                "errors": {"detail": ["El dispositivo está siendo utilizado por una maquina y no puede ser eliminado."]}
            }, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            logging.error("Error al eliminar el dispositivo: %s", str(e), exc_info=True)
            return Response({
                "success": False,
                "code": 500,
                "message": "Error al eliminar el dispositivo.",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
