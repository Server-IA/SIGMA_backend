from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.machinery import Machinery
from machinery.serializers.telemetry_devices_serializers.telemetry_devices_list_serializer import TelemetryDevicesListSerializer
from machinery.serializers.telemetry_devices_serializers.telemetry_devices_create_serializer import TelemetryDevicesCreateSerializer
from machinery.utils.audit_helpers import telemetry_devices_snapshot, telemetry_device_parameter_snapshot, get_actor_info
from audit_sdk import AuditClient
import logging

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
        Usa el serializador de lista para listar y activos, y el de creación para crear.
        """
        if self.action == 'create':
            return TelemetryDevicesCreateSerializer
        elif self.action == 'list' or self.action == 'active':
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
