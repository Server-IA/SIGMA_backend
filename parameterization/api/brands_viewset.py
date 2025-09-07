from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import Brands, BrandsCategory, Statues
from parameterization.serializers.brands_serializers.brands_create_serializer import BrandsCreateSerializer
from parameterization.serializers.brands_serializers.brands_list_serializer import BrandsListSerializer
from django.shortcuts import get_object_or_404


class BrandsViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = BrandsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Marca creada exitosamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        brand = get_object_or_404(Brands, pk=pk)

        serializer = BrandsCreateSerializer(brand, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Marca actualizada exitosamente"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<category_id>\d+)')
    def list_by_category(self, request, category_id=None):
        if not BrandsCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "BrandsCategory not found."}, status=status.HTTP_404_NOT_FOUND)

        brands = Brands.objects.filter(id_brands_categories_id=category_id)
        serializer = BrandsListSerializer(brands, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<category_id>\d+)')
    def list_active_by_category(self, request, category_id=None):
        if not BrandsCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "BrandsCategory not found."}, status=status.HTTP_404_NOT_FOUND)
        marcas = Brands.objects.filter(id_brands_categories_id=category_id, id_statues_id=1)
        if not marcas.exists():
            return Response({
                "message": "No existen marcas activas registradas para esta categoría",
                "data": []
            }, status=status.HTTP_200_OK)
        serializer = BrandsListSerializer(marcas, many=True)
        return Response({
            "message": "Marcas activas por categoría obtenidas exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        brand = get_object_or_404(Brands, pk=pk)

        if brand.id_statues_id == 1:
            try:
                brand.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            message = "Marca desactivada exitosamente"
        else:
            try:
                brand.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            message = "Marca activada exitosamente"

        brand.save(update_fields=['id_statues'])
        return Response({"message": message}, status=status.HTTP_200_OK)


