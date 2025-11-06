import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from service_requests.models.service_request import ServiceRequest
from monitoring.serializers.data_serializer import DataSerializer, get_machinery_data

logger = logging.getLogger(__name__)

class DataViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de datos de telemetría.
    """
    
    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
        """
        # Obtener el payload del JWT desde request.auth
        payload = getattr(request, "auth", None) or {}

        # Obtener roles del payload (soporta "rol" y "roles")
        user_roles = payload.get("rol") or payload.get("roles") or []

        # Extraer todos los IDs de permisos de todos los roles
        permisos_usuario = []
        for rol in user_roles:
            # Obtener permisos del rol (soporta "permisos" y "permissions")
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))

        return required_permission_id in permisos_usuario
    
    @action(detail=True, methods=['get'])
    def by_request(self, request, pk=None):
        """
        Obtiene los datos de telemetría para una solicitud específica.
        Requiere el permiso con ID 171.
        """
        try:
            logger.info(f"Iniciando solicitud de datos para request_id: {pk}")
            
            # Verificar permiso
            logger.debug("Verificando permisos...")
            if not self.check_permission(request, 171):
                logger.warning(f"Acceso denegado para el usuario: {request.user}")
                return Response(
                    {"detail": "No tiene permiso para acceder a este recurso"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
            try:
                # Verificar que la solicitud existe
                logger.debug(f"Buscando solicitud con ID: {pk}")
                request_obj = ServiceRequest.objects.get(id_request=pk)
                logger.debug(f"Solicitud encontrada: {request_obj}")
            except ServiceRequest.DoesNotExist:
                logger.error(f"Solicitud no encontrada: {pk}")
                return Response(
                    {"detail": "Solicitud no encontrada"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener los datos de la maquinaria
            logger.debug("Obteniendo datos de maquinaria...")
            machinery_data = get_machinery_data(pk)
            logger.debug(f"Datos de maquinaria obtenidos: {len(machinery_data)} registros")
            
            # Serializar y retornar los datos
            serializer = DataSerializer(machinery_data, many=True)
            logger.info("Solicitud completada exitosamente")
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"Error en by_request: {str(e)}")
            return Response(
                {"detail": f"Error interno del servidor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # Acción para listar (requerida por DRF)
    def list(self, request):
        return Response(
            {"detail": "Por favor proporcione un ID de solicitud usando la acción 'by_request'"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
