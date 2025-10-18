from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from service_requests.models.texture import Texture

class TextureViewSet(viewsets.ViewSet):
    """
    ViewSet para listar las texturas.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Retorna la lista de todas las texturas.
        """
        try:
            textures = Texture.objects.all().order_by('id')
            data = [{
                'id': t.id,
                'name': t.texture,
                'value': t.value
            } for t in textures]
            return Response({
                'success': True,
                'message': 'Texturas obtenidas exitosamente',
                'data': data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener las texturas',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
