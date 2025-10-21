from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from machinery.models.parameters import Parameters
from machinery.serializers.parameters_serializers.parameters_list_serializer import ParametersListSerializer

class ParametersViewSet(viewsets.ViewSet):
    """
    ViewSet para listar los parámetros.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        listar de parámetros.
        """
        try:
            parameters = Parameters.objects.all().order_by('id')
            serializer = ParametersListSerializer(parameters, many=True)
            return Response({
                'success': True,
                'message': 'Parámetros obtenidos exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener los parámetros',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
