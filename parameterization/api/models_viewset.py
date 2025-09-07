from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from parameterization.models import Models, Brands, Statues
from parameterization.serializers.models_serializers.models_create_serializer import ModelsCreateSerializer
from parameterization.serializers.models_serializers.models_list_serializer import ModelsListSerializer


class ModelsViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = ModelsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Modelo creado exitosamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        model = get_object_or_404(Models, pk=pk)
        serializer = ModelsCreateSerializer(model, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Modelo actualizado exitosamente"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<brand_id>\d+)')
    def list_by_brand(self, request, brand_id=None):
        if not Brands.objects.filter(pk=brand_id).exists():
            return Response({"detail": "Brands not found."}, status=status.HTTP_404_NOT_FOUND)
        modelos = Models.objects.filter(id_brand_id=brand_id)
        serializer = ModelsListSerializer(modelos, many=True)
        return Response({
            "message": "Modelos por marca obtenidos exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<brand_id>\d+)')
    def list_active_by_brand(self, request, brand_id=None):
        if not Brands.objects.filter(pk=brand_id).exists():
            return Response({"detail": "Brands not found."}, status=status.HTTP_404_NOT_FOUND)
        modelos = Models.objects.filter(id_brand_id=brand_id, id_statues_id=1)
        return Response({
            "message": "Modelos activos por marca obtenidos exitosamente",
            "data": ModelsListSerializer(modelos, many=True).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        model = get_object_or_404(Models, pk=pk)
        if model.id_statues_id == 1:
            try:
                model.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            msg = "Modelo desactivado exitosamente"
        else:
            try:
                model.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            msg = "Modelo activado exitosamente"
        model.save(update_fields=['id_statues'])
        return Response({"message": msg}, status=status.HTTP_200_OK)

