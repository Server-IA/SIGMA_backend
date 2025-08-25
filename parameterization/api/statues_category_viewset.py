from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import StatuesCategory
from parameterization.serializers.statues_category_serializers.statues_category_create_serializer import StatuesCategoryCreateSerializer
from parameterization.serializers.statues_category_serializers.statues_category_list_serializer import StatuesCategoryListSerializer

class StatuesCategoryViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = StatuesCategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de estado creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def listar_categorias(self, request):
        categorias = StatuesCategory.objects.all()
        serializer = StatuesCategoryListSerializer(categorias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
