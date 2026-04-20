import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from payroll.models import EmployeeNews
from payroll.serializers.employee_news_serializers.employee_news_list_serializer import EmployeeNewsListSerializer

logger = logging.getLogger(__name__)


class EmployeeNewsViewSet(viewsets.ViewSet):
    """Gestiona las novedades de empleados."""

    def check_permission(self, request, required_permission_id: int) -> bool:
        """Verifica si el usuario tiene el permiso requerido."""
        payload = getattr(request, "auth", None) or {}
        user_roles = payload.get("rol") or payload.get("roles") or []

        permission_ids = []
        for rol in user_roles:
            perms = (rol or {}).get("permisos") or (rol or {}).get("permissions") or []
            for perm in perms:
                perm_id = perm.get("id_permission") or perm.get("id")
                if perm_id:
                    permission_ids.append(perm_id)

        return required_permission_id in permission_ids

    @action(detail=False, methods=['get'], url_path='list')
    def list_employee_news(self, request):
        """
        Lista todas las novedades de empleados.
        Requiere autenticación y permiso con ID 189.
        """
        # Check authentication
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check permission
        required_permission = 189
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para listar novedades de empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Obtener todas las novedades ordenadas por fecha descendente
            news = EmployeeNews.objects.select_related(
                'id_employee',
                'id_employee__id_user',
                'id_responsible_user'
            ).order_by('-news_date')

            serializer = EmployeeNewsListSerializer(
                news,
                many=True,
                context={'request': request}
            )

            return Response(
                {
                    "message": "Novedades obtenidas exitosamente.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Exception as exc:
            logger.exception("Error al listar novedades de empleados")
            return Response(
                {
                    "message": "Ocurrió un error al obtener las novedades.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
