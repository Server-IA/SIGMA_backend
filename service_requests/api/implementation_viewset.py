from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from service_requests.models.implementation import Implementation

class ImplementationViewSet(viewsets.ViewSet):
    """
    ViewSet para listar las implementaciones.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Retorna la lista de todas las implementaciones.
        """
        try:
            implementations = Implementation.objects.all().order_by('id')
            data = [{
                'id': imp.id,
                'name': imp.name,
                'real_name': imp.real_name,
                'k_base': imp.k_base,
                'n': imp.n
            } for imp in implementations]
            return Response({
                'success': True,
                'message': 'Implementaciones obtenidas exitosamente',
                'data': data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener las implementaciones',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
