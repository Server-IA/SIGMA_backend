from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import UserVisualParameterization
from parameterization.serializers.user_visual_parameterization_serializers.user_visual_parameterization_create_serializer import UserVisualParameterizationCreateSerializer
from parameterization.serializers.user_visual_parameterization_serializers.user_visual_parameterization_list_serializer import UserVisualParameterizationListSerializer
from parameterization.serializers.user_visual_parameterization_serializers.user_visual_parameterization_update_serializer import UserVisualParameterizationUpdateSerializer

class UserVisualParameterizationViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = UserVisualParameterizationCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Asignación de parametrización visual al usuario creada exitosamente",
                    "status": "success"
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    "message": f"Error al crear la asignación: {str(e)}",
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
            instance = UserVisualParameterization.objects.get(pk=pk)
        except UserVisualParameterization.DoesNotExist:
            return Response({
                "message": "Asignación no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = UserVisualParameterizationListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        try:
            instance = UserVisualParameterization.objects.get(pk=pk)
        except UserVisualParameterization.DoesNotExist:
            return Response({
                "message": "Asignación no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UserVisualParameterizationUpdateSerializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Asignación actualizada exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar la asignación: {str(e)}",
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
            instance = UserVisualParameterization.objects.get(pk=pk)
        except UserVisualParameterization.DoesNotExist:
            return Response({
                "message": "Asignación no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UserVisualParameterizationUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Asignación actualizada exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar la asignación: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def listar_asignaciones(self, request):
        asignaciones = UserVisualParameterization.objects.all()
        serializer = UserVisualParameterizationListSerializer(asignaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
