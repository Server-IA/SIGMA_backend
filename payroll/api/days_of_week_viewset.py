from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from payroll.models.days_of_week import DaysOfWeek

class DaysOfWeekViewSet(viewsets.ViewSet):
    """
    ViewSet para listar los días de la semana.
    Requiere autenticación pero no permisos específicos.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Lista todos los días de la semana disponibles.

        Returns:
            JSON con la lista de días de la semana
        """
        try:
            days = DaysOfWeek.objects.all().order_by('id_day_of_week')
            data = [{
                'id': day.id_day_of_week,
                'name': day.name
            } for day in days]
            
            return Response({
                'success': True,
                'message': 'Días de la semana obtenidos exitosamente',
                'data': data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al obtener los días de la semana',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
