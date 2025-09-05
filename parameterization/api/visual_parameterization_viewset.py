from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import VisualParameterization
from parameterization.serializers.visual_parameterization_serializers.visual_parameterization_create_serializer import VisualParameterizationCreateSerializer
from parameterization.serializers.visual_parameterization_serializers.visual_parameterization_list_serializer import VisualParameterizationListSerializer
from parameterization.serializers.visual_parameterization_serializers.visual_parameterization_update_serializer import VisualParameterizationUpdateSerializer

class VisualParameterizationViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = VisualParameterizationCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Parametrización visual creada exitosamente",
                    "status": "success"
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    "message": f"Error al crear la parametrización visual: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        try:
            instance = VisualParameterization.objects.get(pk=pk)
        except VisualParameterization.DoesNotExist:
            return Response({
                "message": "Parametrización visual no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = VisualParameterizationListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        try:
            instance = VisualParameterization.objects.get(pk=pk)
        except VisualParameterization.DoesNotExist:
            return Response({
                "message": "Parametrización visual no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = VisualParameterizationUpdateSerializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Parametrización visual actualizada exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar la parametrización visual: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        try:
            instance = VisualParameterization.objects.get(pk=pk)
        except VisualParameterization.DoesNotExist:
            return Response({
                "message": "Parametrización visual no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = VisualParameterizationUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Parametrización visual actualizada exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar la parametrización visual: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def listar_parametrizaciones(self, request):
        parametrizaciones = VisualParameterization.objects.all()
        serializer = VisualParameterizationListSerializer(parametrizaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
