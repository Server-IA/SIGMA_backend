from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from machinery.models.machinery import Machinery
from parameterization.models import Statues
from machinery.serializers.machinery_serializers.machinery_general_sheet_create_serializer import (
    MachineryGeneralSheetCreateSerializer
)
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class MachineryViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de maquinaria.
    """

    @action(detail=False, methods=['post'], url_path='create-general-sheet')
    @parser_classes([MultiPartParser, FormParser])
    def create_machinery_general_sheet(self, request):
        """
        Crea una nueva ficha general de maquinaria.

        Campos obligatorios:
        - machinery_name: Nombre de la maquinaria (único)
        - serial_number: Número de serie (único)
        - machinery_type: ID del tipo de maquinaria
        - id_model: ID del modelo
        - machinery_secondary_type: ID del subtipo de maquinaria
        - responsible_user: ID del usuario responsable
        
        Para la imagen de perfil:
        - image_path: Archivo de imagen (opcional, formatos: JPEG, JPG, PNG, máximo 5MB)

        Campos opcionales:
        - manufacturing_year: Año de fabricación
        - tariff_subheading: Partida arancelaria
        - id_device: ID del dispositivo de telemetría (opcional)
        """
        try:
            serializer = MachineryGeneralSheetCreateSerializer(
                data=request.data, 
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Maquinaria y ficha general creada exitosamente",
                        "data": serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
                
            logger.warning(f"Error de validación: {serializer.errors}")
            return Response(
                {
                    "error": "Error de validación",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {
                    "error": "Error al crear la ficha de maquinaria",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )