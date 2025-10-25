from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from machinery.models.event_types import EventTypes
from machinery.serializers.event_types_serializers.event_types_serializer import EventTypesSerializer

class EventTypesViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar operaciones con tipos de eventos.
    Permite listar todos los tipos de eventos disponibles.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Lista todos los tipos de eventos disponibles.

        Returns:
            JSON con la lista de tipos de eventos
        """
        try:
            event_types = EventTypes.objects.all().order_by('id_event_type')
            serializer = EventTypesSerializer(event_types, many=True)
            return Response({
                'success': True,
                'message': 'Tipos de eventos obtenidos exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener los tipos de eventos',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
