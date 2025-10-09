from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from service_requests.models.person_type import PersonType

class PersonTypeViewSet(viewsets.ViewSet):
    """
    ViewSet para listar los tipos de personas.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Retorna la lista de todos los tipos de personas.
        """
        try:
            person_types = PersonType.objects.all().order_by('id_person_type')
            data = [{
                'id': pt.id_person_type,
                'name': pt.name
            } for pt in person_types]
            return Response({
                'success': True,
                'message': 'Tipos de persona obtenidos exitosamente',
                'data': data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener los tipos de persona',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
