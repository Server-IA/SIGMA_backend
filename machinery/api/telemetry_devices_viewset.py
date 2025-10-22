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

    @action(detail=True, methods=['patch'])
    def deactivate(self, request, pk=None):
        
        # Autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 201
        if not self.check_permission(request, permission_id):
            return Response({"message": "No tiene permisos para desactivar dispositivos de telemetría."}, status=status.HTTP_403_FORBIDDEN)

        device = get_object_or_404(TelemetryDevices, pk=pk)

        inactive_status = self._get_status_by_name("Inactivo")
        if not inactive_status:
            return Response({"message": "No se encontró el estado 'Inactivo' en la parametrización."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Si ya está inactivo, retornamos 409 o idempotente 200. Aquí elegimos 409 para visibilidad.
        if getattr(device, 'id_statues_id', None) == getattr(inactive_status, 'id_statues', None):
            return Response({"message": "El dispositivo ya está inactivo."}, status=status.HTTP_409_CONFLICT)

        try:
            with transaction.atomic():
                device.id_statues = inactive_status
                device.save(update_fields=["id_statues", "modification_date"])

                logging.info(
                    "audit: telemetry_device.deactivate",
                    extra={
                        "action": "soft_delete",
                        "id_device": device.id_device,
                        "name": device.name,
                        "user_id": getattr(request.user, 'id', None),
                    }
                )

            serializer = TelemetryDevicesListSerializer(device)
            return Response({"message": "Dispositivo desactivado correctamente.", "device": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "No se pudo completar la desactivación.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
      
        # Autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 200
        if not self.check_permission(request, permission_id):
            return Response({"message": "No tiene permisos para eliminar dispositivos de telemetría."}, status=status.HTTP_403_FORBIDDEN)

        device = get_object_or_404(TelemetryDevices, pk=pk)

        # Verificar dependencias (asignación a maquinaria)
        has_dependencies = Machinery.objects.filter(id_device_id=device.id_device).exists()

        if has_dependencies:
            # Soft delete -> estado Inactivo
            inactive_status = self._get_status_by_name("Inactivo")
            if not inactive_status:
                return Response({"message": "No se encontró el estado 'Inactivo' en la parametrización."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Si ya está inactivo, devolvemos 409 para indicar que no procede eliminar físicamente
            if getattr(device, 'id_statues_id', None) == getattr(inactive_status, 'id_statues', None):
                return Response({"message": "El dispositivo ya se encuentra inactivo. No es posible eliminación física por dependencias."}, status=status.HTTP_409_CONFLICT)

            try:
                with transaction.atomic():
                    device.id_statues = inactive_status
                    device.save(update_fields=["id_statues", "modification_date"])

                    logging.info(
                        "audit: telemetry_device.soft_delete",
                        extra={
                            "action": "soft_delete",
                            "reason": "dependencies_present",
                            "id_device": device.id_device,
                            "name": device.name,
                            "user_id": getattr(request.user, 'id', None),
                        }
                    )

                serializer = TelemetryDevicesListSerializer(device)
                return Response({
                    "message": "El dispositivo tiene información relacionada. Se realizó desactivación lógica.",
                    "device": serializer.data
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"message": "No se pudo completar la desactivación lógica.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Sin dependencias -> hard delete
        try:
            with transaction.atomic():
                device_id = device.id_device
                device_name = device.name
                device.delete()

                logging.info(
                    "audit: telemetry_device.hard_delete",
                    extra={
                        "action": "hard_delete",
                        "id_device": device_id,
                        "name": device_name,
                        "user_id": getattr(request.user, 'id', None),
                    }
                )

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"message": "No se pudo completar la eliminación.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
