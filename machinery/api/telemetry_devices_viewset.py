from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.machinery import Machinery
from machinery.serializers.telemetry_devices_serializers.telemetry_devices_list_serializer import TelemetryDevicesListSerializer
from django.db import transaction
from django.shortcuts import get_object_or_404
from parameterization.models.statues import Statues
import logging
from django.db import IntegrityError
from django.http import Http404
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info, telemetry_device_snapshot

class TelemetryDevicesViewSet(viewsets.ModelViewSet):
    

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

    queryset = TelemetryDevices.objects.all()
    
    def get_serializer_class(self):
        
        if self.action == 'list' or self.action == 'active':
            return TelemetryDevicesListSerializer
        return TelemetryDevicesListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # If the request is for active devices, only return active devices (status ID 1)
        if self.action == 'active':
            return queryset.filter(id_statues=1).order_by('name')
            
        # For list view, return only active devices (status ID 1) that are not assigned to any machinery
        # Get all devices that are assigned to any machinery
        used_device_ids = list(Machinery.objects.exclude(
            id_device_id=""
        ).values_list('id_device_id', flat=True).distinct())
        
        # Return active devices that are not in the used_device_ids list
        return queryset.filter(
            id_statues=1
        ).exclude(
            id_device__in=used_device_ids
        ).order_by('name')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
       
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
            before = telemetry_device_snapshot(device)
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
                        after=telemetry_device_snapshot(device),
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
                before = telemetry_device_snapshot(device)
                device.delete()

                logging.info(
                    "audit: telemetry_device.hard_delete",
                    extra={
                        "action": "hard_delete",
                        "id_device": before.get("id_device"),
                        "name": before.get("name"),
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
                "message": "Dispositivo eliminado correctamente.",
                "data": None
            }, status=status.HTTP_200_OK)
        except IntegrityError as e:
            logging.error("Error de integridad al eliminar dispositivo: %s", str(e), exc_info=True)
            return Response({
                "success": False,
                "code": 409,
                "message": "No se puede eliminar el dispositivo porque tiene referencias asociadas.",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            logging.error("Error al eliminar el dispositivo: %s", str(e), exc_info=True)
            return Response({
                "success": False,
                "code": 500,
                "message": "Error al eliminar el dispositivo.",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
