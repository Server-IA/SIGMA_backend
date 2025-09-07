from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import BrandsCategory
from parameterization.serializers.brands_category_serializers.brands_category_create_serializer import BrandsCategoryCreateSerializer
from parameterization.serializers.brands_category_serializers.brands_category_list_serializer import BrandsCategoryListSerializer


class BrandsCategoryViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = BrandsCategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de marca creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            categoria = BrandsCategory.objects.get(pk=pk)
        except BrandsCategory.DoesNotExist:
            return Response({"error": "Categoría no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BrandsCategoryCreateSerializer(categoria, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de marca actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def listar_categorias(self, request):
        categorias = BrandsCategory.objects.all()
        serializer = BrandsCategoryListSerializer(categorias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


