from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from parameterization.models.units import Units
from parameterization.serializers.units_serializers.units_create_serializer import UnitsCreateSerializer
from parameterization.serializers.units_serializers.units_list_serializer import UnitsListSerializer


class UnitsViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = UnitsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Unidad creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        units = Units.objects.all()
        if not units.exists():
            return Response({
                "message": "No existen unidades registradas",
                "data": []
            }, status=status.HTTP_200_OK)
        serializer = UnitsListSerializer(units, many=True)
        return Response({
            "message": "Unidades obtenidas exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        unit = get_object_or_404(Units, pk=pk)
        serializer = UnitsListSerializer(unit)
        return Response({
            "message": "Unidad obtenida exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        unit = get_object_or_404(Units, pk=pk)
        serializer = UnitsCreateSerializer(unit, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Unidad actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        unit = get_object_or_404(Units, pk=pk)
        serializer = UnitsCreateSerializer(unit, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Unidad actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<category_id>\d+)')
    def list_by_category(self, request, category_id=None):
        units = Units.objects.filter(id_units_categories_id=category_id)
        if not units.exists():
            return Response({
                "message": "No existen unidades registradas para esta categoría",
                "data": []
            }, status=status.HTTP_200_OK)
        serializer = UnitsListSerializer(units, many=True)
        return Response({
            "message": "Unidades por categoría obtenidas exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


