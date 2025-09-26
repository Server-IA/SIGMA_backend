from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.serializers.telemetry_devices_serializers.telemetry_devices_list_serializer import TelemetryDevicesListSerializer

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
        Usa el serializador de lista para listar y activos.
        """
        if self.action == 'list' or self.action == 'active':
            return TelemetryDevicesListSerializer
        return TelemetryDevicesListSerializer
    
    def get_queryset(self):
        return super().get_queryset().order_by('name')
    
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
                {"message": "No tiene permisos para listar maquinaria"},
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
