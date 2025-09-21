from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from machinery.models import SpecificTechnicalSheet, Machinery
from parameterization.models import Statues
from machinery.serializers.machinery_serializers.machinery_specific_sheet_create_serializer import SpecificTechnicalSheetCreateSerializer

class SpecificTechnicalSheetViewSet(viewsets.ModelViewSet):
    queryset = SpecificTechnicalSheet.objects.all()
    serializer_class = SpecificTechnicalSheetCreateSerializer

    def create(self, request, *args, **kwargs):
        """
        Crea la ficha técnica específica y actualiza el estado de la maquinaria.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                # Crear la ficha técnica
                sheet = serializer.save()

                # Obtener maquinaria asociada
                machinery = sheet.id_machinery

                # Estado de maquinaria en "registro completado" (id = 4, ejemplo)
                try:
                    operational_status = Statues.objects.get(id_statues=4)
                except Statues.DoesNotExist:
                    return Response(
                        {"error": "No se encontró el estado de 'registro completado'"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Actualizar estado de la maquinaria
                machinery.machinery_operational_status = operational_status
                machinery.save(update_fields=["machinery_operational_status"])

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as e:
            return Response(
                {"error": f"Ocurrió un error al crear la ficha técnica específica: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )