from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import VisualParameterization, Statues
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

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        try:
            parametrizacion = VisualParameterization.objects.get(pk=pk)
        except VisualParameterization.DoesNotExist:
            return Response(
                {"error": "Parametrización visual no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Se asume que 1 = Activo, 2 = Inactivo
        if parametrizacion.visual_parameterization_status_id == 1:
            try:
                parametrizacion.visual_parameterization_status = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response(
                    {"error": "El estado con id=2 no existe"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            message = "Parametrización visual desactivada exitosamente"
        else:
            try:
                parametrizacion.visual_parameterization_status = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response(
                    {"error": "El estado con id=1 no existe"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            message = "Parametrización visual activada exitosamente"

        parametrizacion.save(update_fields=['visual_parameterization_status'])
        return Response({"message": message}, status=status.HTTP_200_OK)
