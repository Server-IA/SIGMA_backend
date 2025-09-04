from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import Types, TypesCategory, Statues
from parameterization.serializers.types_serializers.types_create_serializer import TypesCreateSerializer
from parameterization.serializers.types_serializers.types_list_serializer import TypesListSerializer


class TypesViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = TypesCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Tipo creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            tipo = Types.objects.get(pk=pk)
        except Types.DoesNotExist:
            return Response(
                {"error": "Tipo no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TypesCreateSerializer(tipo, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Tipo actualizado exitosamente"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<category_id>\d+)')
    def listar_por_categoria(self, request, category_id=None):
        if not TypesCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "TypesCategory not found."},
                            status=status.HTTP_404_NOT_FOUND)

        tipos = Types.objects.filter(id_types_categories_id=category_id)
        serializer = TypesListSerializer(tipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<category_id>\d+)')
    def listar_activos_por_categoria(self, request, category_id=None):
        if not TypesCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "TypesCategory not found."},
                            status=status.HTTP_404_NOT_FOUND)
        tipos = Types.objects.filter(
            id_types_categories_id=category_id,
            id_statues_id=1
        )
        serializer = TypesListSerializer(tipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):

        try:
            tipo = Types.objects.get(pk=pk)
        except Types.DoesNotExist:
            return Response(
                {"error": "Tipo no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        if tipo.id_statues_id == 1:
            try:
                tipo.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Tipo desactivado exitosamente"
        else:
            try:
                tipo.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Tipo activado exitosamente"

        tipo.save(update_fields=['id_statues'])
        return Response({"message": message}, status=status.HTTP_200_OK)