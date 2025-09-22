from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from machinery.models import SpecificTechnicalSheet, Machinery
from machinery.serializers.machinery_serializers.machinery_specific_sheet_create_serializer import SpecificTechnicalSheetCreateSerializer

class SpecificTechnicalSheetViewSet(viewsets.ModelViewSet):
    queryset = SpecificTechnicalSheet.objects.all()
    serializer_class = SpecificTechnicalSheetCreateSerializer

    def create(self, request, *args, **kwargs):
        """
        Crea la ficha técnica específica y actualiza el estado de la maquinaria.
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
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": "Error inesperado al crear la ficha técnica específica",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )