from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from machinery.models import SpecificTechnicalSheet, Machinery
from machinery.serializers.machinery_serializers.machinery_specific_sheet_create_serializer import SpecificTechnicalSheetCreateSerializer
from rest_framework import serializers

class SpecificTechnicalSheetViewSet(viewsets.ModelViewSet):
    queryset = SpecificTechnicalSheet.objects.all()
    serializer_class = SpecificTechnicalSheetCreateSerializer
    http_method_names = ["get", "post", "put"]

    def create(self, request, *args, **kwargs):
        """
        Crea la ficha técnica específica.
        Valida que no exista ya una ficha técnica para la máquina especificada.
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                sheet = serializer.save()

            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    "success": True,
                    "message": "Ficha técnica específica creada exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
            
        except serializers.ValidationError as e:
            # Captura errores de validación del serializador
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "errors": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Captura cualquier otro error inesperado
            return Response(
                {
                    "success": False,
                    "message": "Error inesperado al crear la ficha técnica específica",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        Actualiza la ficha técnica específica.
        No permite actualizar el ID de la maquinaria.
        Actualiza automáticamente la fecha de modificación y el usuario que realizó la modificación.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Hacer una copia de los datos de la solicitud
        data = request.data.copy()
        
        # Si se incluye id_machinery, lo reemplazamos por el valor actual de la instancia
        # para evitar que se modifique pero cumplir con la validación del serializador
        if 'id_machinery' in data:
            data['id_machinery'] = instance.id_machinery_id
            
        serializer = self.get_serializer(instance, data=data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                # Actualizar la fecha de modificación y el usuario responsable
                instance.modification_date = timezone.now()
                if request.user and request.user.is_authenticated:
                    instance.id_responsible_user = request.user
                instance.save()
                
                # Guardar el resto de los datos del serializer
                serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Ficha técnica específica actualizada exitosamente"
                },
                status=status.HTTP_200_OK,
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "errors": e.detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Error inesperado al actualizar la ficha técnica específica",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )