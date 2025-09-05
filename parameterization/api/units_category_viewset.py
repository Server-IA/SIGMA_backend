from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from parameterization.models.units_category import UnitsCategory
from parameterization.serializers.units_category_serializers.units_category_create_serializer import UnitsCategoryCreateSerializer
from parameterization.serializers.units_category_serializers.units_category_list_serializer import UnitsCategoryListSerializer


class UnitsCategoryViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = UnitsCategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de métricas de medida creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        """Consultar todas las categorías de métricas de medida"""
        categories = UnitsCategory.objects.all()
        if not categories.exists():
            return Response({
                "message": "No existen categorías de unidades de medida registradas",
                "data": []
            }, status=status.HTTP_200_OK)
        
        serializer = UnitsCategoryListSerializer(categories, many=True)
        return Response({
            "message": "Categorías de unidades de medida obtenidas exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Consultar categoría de métricas de medida por ID"""
        category = get_object_or_404(UnitsCategory, pk=pk)
        serializer = UnitsCategoryListSerializer(category)
        return Response({
            "message": "Categoría de unidades de medida obtenida exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        """Actualizar categoría de métricas de medida por ID (PUT)"""
        category = get_object_or_404(UnitsCategory, pk=pk)
        serializer = UnitsCategoryCreateSerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de métricas de medida actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """Actualizar parcialmente categoría de métricas de medida por ID (PATCH)"""
        category = get_object_or_404(UnitsCategory, pk=pk)
        serializer = UnitsCategoryCreateSerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de métricas de medida actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def list_units_categories(self, request):
        categories = UnitsCategory.objects.all()
        if not categories.exists():
            return Response({
                "message": "No existen categorías de unidades de medida registradas",
                "data": []
            }, status=status.HTTP_200_OK)
        
        serializer = UnitsCategoryListSerializer(categories, many=True)
        return Response({
            "message": "Categorías de unidades de medida obtenidas exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


