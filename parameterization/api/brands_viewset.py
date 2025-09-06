from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import Brands, BrandsCategory
from parameterization.serializers.brands_serializers.brands_create_serializer import BrandsCreateSerializer
from parameterization.serializers.brands_serializers.brands_list_serializer import BrandsListSerializer


class BrandsViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = BrandsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Marca creada exitosamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            brand = Brands.objects.get(pk=pk)
        except Brands.DoesNotExist:
            return Response({"error": "Marca no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BrandsCreateSerializer(brand, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Marca actualizada exitosamente"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<category_id>\d+)')
    def list_by_category(self, request, category_id=None):
        if not BrandsCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "BrandsCategory not found."},
                            status=status.HTTP_404_NOT_FOUND)
        marcas = Brands.objects.filter(id_brands_categories_id=category_id)
        serializer = BrandsListSerializer(marcas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<category_id>\d+)')
    def list_active_by_category(self, request, category_id=None):
        if not BrandsCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "BrandsCategory not found."},
                            status=status.HTTP_404_NOT_FOUND)
        marcas = Brands.objects.filter(id_brands_categories_id=category_id, id_statues_id=1)
        serializer = BrandsListSerializer(marcas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


