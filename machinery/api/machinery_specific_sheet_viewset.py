from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from machinery.models import SpecificTechnicalSheet, Machinery
from machinery.serializers.machinery_serializers.machinery_specific_sheet_create_serializer import SpecificTechnicalSheetCreateSerializer
from rest_framework import serializers

class SpecificTechnicalSheetViewSet(viewsets.ModelViewSet):
    queryset = SpecificTechnicalSheet.objects.all()
    serializer_class = SpecificTechnicalSheetCreateSerializer

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
        Actualiza una ficha técnica específica existente (PUT o PATCH).
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                serializer.save()

            return Response(
                {
                    "success": True,
                    "message": "Ficha técnica específica actualizada exitosamente",
                    "data": serializer.data,
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

    def partial_update(self, request, *args, **kwargs):
        """
        Actualiza parcialmente una ficha técnica específica existente (PATCH).
        """
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)