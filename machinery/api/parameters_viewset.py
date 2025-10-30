from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
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

    @action(detail=False, methods=['get'], url_path='available')
    def list_available_parameters(self, request):
        """
        Lista parámetros disponibles para configuración de tolerancia.
        Excluye los parámetros con IDs: 1, 2, 4, 5, 13, 16, 17, 18
        Requiere solo autenticación, sin permisos específicos.
        """
        try:
            excluded_ids = [1, 2, 4, 5, 13, 16, 17, 18]
            parameters = Parameters.objects.exclude(id__in=excluded_ids).order_by('id')

            serializer = ParametersListSerializer(parameters, many=True)
            return Response({
                'success': True,
                'message': 'Parámetros disponibles obtenidos exitosamente',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener los parámetros disponibles',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
