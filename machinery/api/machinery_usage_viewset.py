from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from machinery.models.machinery_usage_sheet import MachineryUsageSheet
from machinery.serializers.machinery_serializers.machinery_usage_sheet_create_serializer import MachineryUsageSheetCreateSerializer
from machinery.serializers.machinery_serializers.machinery_usage_sheet_update_serializer import MachineryUsageSheetUpdateSerializer
from django.shortcuts import get_object_or_404
import logging


logger = logging.getLogger(__name__)


class MachineryUsageViewSet(viewsets.ModelViewSet):
    queryset = MachineryUsageSheet.objects.all()
    serializer_class = MachineryUsageSheetCreateSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], url_path='create')
    def create_machinery_usage(self, request):
        try:
            data = request.data.dict() if hasattr(request.data, 'getlist') else request.data
            serializer = self.get_serializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Ficha de uso registrada exitosamente."}, status=status.HTTP_201_CREATED)

            return Response({"success": False, "message": "Error de validación", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error al registrar ficha de uso: {str(e)}")
            return Response({"success": False, "message": "Error al registrar la información de uso de la maquinaria", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    @action(detail=True, methods=['put', 'patch'], url_path='update')
    def update_machinery_usage(self, request, pk=None):
        """
        Actualiza la información de uso de una maquinaria (HU-MAQ-013).
        Requiere responsible_user y justification.
        """
        try:
            usage_instance = get_object_or_404(MachineryUsageSheet, pk=pk)

            serializer = MachineryUsageSheetUpdateSerializer(
                usage_instance,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Información de uso actualizada correctamente"}, status=status.HTTP_200_OK)

            return Response({"success": False, "message": "Error de validación al actualizar la información de uso", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except MachineryUsageSheet.DoesNotExist:
            return Response({"success": False, "message": "La ficha de uso no existe"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al actualizar la información de uso: {str(e)}")
            return Response({"success": False, "message": "Error al actualizar la información de uso de la maquinaria", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)

