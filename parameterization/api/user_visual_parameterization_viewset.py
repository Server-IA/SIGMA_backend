from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import UserVisualParameterization
from parameterization.serializers.user_visual_parameterization_serializers.user_visual_parameterization_create_serializer import UserVisualParameterizationCreateSerializer
from parameterization.serializers.user_visual_parameterization_serializers.user_visual_parameterization_list_serializer import UserVisualParameterizationListSerializer

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

    @action(detail=False, methods=['get'], url_path='list')
    def listar_asignaciones(self, request):
        asignaciones = UserVisualParameterization.objects.all()
        serializer = UserVisualParameterizationListSerializer(asignaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
