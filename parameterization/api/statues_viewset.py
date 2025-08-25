from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import Statues, StatuesCategory
from parameterization.serializers.statues_serializers.statues_create_serializer import StatuesCreateSerializer
from parameterization.serializers.statues_serializers.statues_list_serializer import StatuesListSerializer

class StatuesViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = StatuesCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Estado creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<category_id>\d+)')
    def listar_por_categoria(self, request, category_id=None):
        if not StatuesCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "StatuesCategory not found."}, status=status.HTTP_404_NOT_FOUND)

        estados = Statues.objects.filter(id_statues_categories_id=category_id)
        serializer = StatuesListSerializer(estados, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
