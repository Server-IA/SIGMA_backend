from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models.types_category import TypesCategory
from parameterization.serializers.types_category_serializers.types_category_create_serializer import TypesCategoryCreateSerializer
from parameterization.serializers.types_category_serializers.types_category_list_serializer import TypesCategoryListSerializer


class TypesCategoryViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = TypesCategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de tipo creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            categoria = TypesCategory.objects.get(pk=pk)
        except TypesCategory.DoesNotExist:
            return Response({"error": "Categoría no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TypesCategoryCreateSerializer(categoria, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de tipo actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def listar_categorias(self, request):
        categorias = TypesCategory.objects.all()
        serializer = TypesCategoryListSerializer(categorias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
