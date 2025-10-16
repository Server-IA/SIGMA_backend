from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from service_requests.models.payment_method import PaymentMethod

class PaymentMethodViewSet(viewsets.ViewSet):
    """
    ViewSet para listar los métodos de pago disponibles.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Retorna la lista de todos los métodos de pago.
        """
        try:
            payment_methods = PaymentMethod.objects.all()
            data = [{
                'code': pm.code,
                'name': pm.name
            } for pm in payment_methods]
            return Response({
                'success': True,
                'message': 'Métodos de pago obtenidos exitosamente',
                'data': data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener los métodos de pago',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
