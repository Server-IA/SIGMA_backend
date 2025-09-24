from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.serializers.telemetry_devices_serializers.telemetry_devices_list_serializer import TelemetryDevicesListSerializer

class TelemetryDevicesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo TelemetryDevices.
    """
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
        try:
            queryset = self.get_queryset().filter(id_statues_id=1)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
