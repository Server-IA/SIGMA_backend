from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from service_requests.models.tax_regime import TaxRegime

class TaxRegimeViewSet(viewsets.ViewSet):
    """
    ViewSet para listar los regímenes fiscales.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Retorna la lista de todos los regímenes fiscales.
        """
        try:
            tax_regimes = TaxRegime.objects.all().order_by('id_tax_regime')
            data = [{
                'id': tr.id_tax_regime,
                'code': tr.code,
                'name': tr.name
            } for tr in tax_regimes]
            return Response({
                'success': True,
                'message': 'Regímenes fiscales obtenidos exitosamente',
                'data': data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener los regímenes fiscales',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
