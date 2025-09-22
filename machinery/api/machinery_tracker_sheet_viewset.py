from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from machinery.models.machinery_tracker_sheet import MachineryTrackerSheet
from machinery.serializers.machinery_serializers.machinery_tracker_sheet_create_serializer import MachineryTrackerSheetCreateSerializer
import logging


logger = logging.getLogger(__name__)

class MachineryTrackerViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar el modelo MachineryTracker.
    """
    queryset = MachineryTrackerSheet.objects.all()
    serializer_class = MachineryTrackerSheetCreateSerializer
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], url_path='create')
    def create_machinery_tracker(self, request):
        """
        Crea un registro de MachineryTracker
        """
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "success": True,
                        "message": "MachineryTrackerSheet creado exitosamente",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creando MachineryTracker: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al crear MachineryTrackerSheet",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
