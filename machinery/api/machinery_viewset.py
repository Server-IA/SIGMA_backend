from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from machinery.models.machinery import Machinery
from parameterization.models import Statues
from machinery.serializers.machinery_serializers.machinery_general_sheet_create_serializer import (
    MachineryGeneralSheetCreateSerializer
)
from machinery.serializers.machinery_serializers.machinery_list_serializer import MachineryListSerializer
from django.db.models import Q
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class MachineryViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de maquinaria.
    """
    
    @action(detail=False, methods=['get'], url_path='list')
    def list_machinery(self, request):
        """
        Lista todas las máquinas con información básica.
        
        Incluye:
        - image_path: Ruta de la imagen de la máquina
        - machinery_name: Nombre de la máquina
        - serial_number: Número de serie
        - machinery_secondary_type: ID y nombre del subtipo de maquinaria
        - acquisition_date: Fecha de adquisición (de la ficha de uso)
        - machinery_operational_status: ID y nombre del estado operativo
        """
        try:
            queryset = Machinery.objects.select_related(
                'machinery_secondary_type',
                'machinery_operational_status'
            ).prefetch_related(
                'machineryusagesheet_set'  # Default related_name for the reverse relation
            ).all()
            
            serializer = MachineryListSerializer(queryset, many=True, context={'request': request})
            
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error listing machinery: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': 'Error al listar la maquinaria',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
                        "success": True,
                        "message": "Maquinaria y ficha general creada exitosamente",
                        "machinery_id": serializer.instance.id_machinery
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
            return Response(
                {
                    "success": False,
                    "message": "Error al crear la ficha de maquinaria",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='confirm-registration')
    def confirm_registration(self, request, pk=None):
        """
        Confirma el registro de una maquinaria cambiando su estado de "En Registro" (id=3) a "Activo" (id=4).
        
        Este endpoint:
        1. Valida que la maquinaria existe
        2. Verifica que está en estado "En Registro" (id=3)
        3. Cambia el estado a "Activo" (id=4)
        4. Actualiza automáticamente la fecha de modificación
        """
        try:
            # Obtener la maquinaria por ID
            machinery = Machinery.objects.get(pk=pk)
            
            # Validar que está en estado "En Registro" (id=3)
            if machinery.machinery_operational_status.id_statues != 3:
                return Response(
                    {
                        "success": False,
                        "message": "La maquinaria no está en estado de registro",
                        "details": f"Estado actual: {machinery.machinery_operational_status.name if hasattr(machinery.machinery_operational_status, 'name') else machinery.machinery_operational_status.id_statues}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener el estado "Activo" (id=4)
            try:
                active_status = Statues.objects.get(id_statues=4)
            except Statues.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Estado activo no encontrado en el sistema",
                        "details": "No existe un estado con id=4"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Cambiar el estado a "Activo"
            machinery.machinery_operational_status = active_status
            machinery.save()  # Esto actualiza modification_date automáticamente
            
            return Response(
                {
                    "success": True,
                    "message": "Registro de maquinaria confirmado exitosamente",
                    "data": {
                        "machinery_id": machinery.id_machinery,
                        "machinery_name": machinery.machinery_name,
                        "new_status": active_status.id_statues,
                        "modification_date": machinery.modification_date
                    }
                },
                status=status.HTTP_200_OK
            )
            
        except Machinery.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Maquinaria no encontrada",
                    "details": f"No existe una maquinaria con ID {pk}"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al confirmar registro de maquinaria {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error interno al confirmar el registro",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )