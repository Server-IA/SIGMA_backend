from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from service_requests.models.soil_type import SoilType

class SoilTypeViewSet(viewsets.ViewSet):
    """
    ViewSet para listar los tipos de suelo.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Retorna la lista de todos los tipos de suelo.
        """
        try:
            soil_types = SoilType.objects.all().order_by('id')
            data = [{
                'id': st.id,
                'surface': st.surface,
                'low': st.low,
                'medium': st.medium,
                'high': st.high,
                'very_high': st.very_high
            } for st in soil_types]
            return Response({
                'success': True,
                'message': 'Tipos de suelo obtenidos exitosamente',
                'data': data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener los tipos de suelo',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
