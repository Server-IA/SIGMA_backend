import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from service_requests.models.service_request import ServiceRequest
from monitoring.serializers.data_serializer import DataSerializer, get_machinery_data
from monitoring.serializers.service_request_machinery_serializer import ServiceRequestMachineryDataSerializer

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
    
    @action(detail=False, methods=['get'])
    def service_requests(self, request):
        """
        Obtiene el listado de solicitudes de servicio con información de maquinarias y operadores.
        Requiere el permiso con ID 172.
        
        Filtros opcionales:
        - status: Filtrar por estado (20: Programada, 21: En Progreso, 22: Finalizada)
        - customer_id: Filtrar por ID de cliente
        - start_date: Fecha de inicio (formato YYYY-MM-DD)
        - end_date: Fecha de fin (formato YYYY-MM-DD)
        - machinery_id: ID de la maquinaria a filtrar (opcional)
        - operator_id: ID del operador a filtrar (opcional)
        
        Se pueden combinar los filtros de la siguiente manera:
        - Solo machinery_id: Trae solo las solicitudes con esa maquinaria
        - Solo operator_id: Trae solo las solicitudes con ese operador
        - Ambos: Trae solo las solicitudes donde ese operador está asignado a esa maquinaria
        """
        try:
            # Verificar permiso
            if not self.check_permission(request, 172):
                return Response(
                    {"error": "No tiene permiso para ver las solicitudes de servicio"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Obtener parámetros de filtro
            status_filter = request.query_params.get('status')
            customer_id = request.query_params.get('customer_id')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            machinery_id = request.query_params.get('machinery_id')
            operator_id = request.query_params.get('operator_id')
            
            # Convertir a enteros si existen
            if machinery_id is not None:
                try:
                    machinery_id = int(machinery_id)
                except (ValueError, TypeError):
                    return Response(
                        {"detail": "El parámetro machinery_id debe ser un número entero"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if operator_id is not None:
                try:
                    operator_id = int(operator_id)
                except (ValueError, TypeError):
                    return Response(
                        {"detail": "El parámetro operator_id debe ser un número entero"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Construir consulta base
            from service_requests.models.request_machinery_user import RequestMachineryUser
            
            # Obtener los IDs de solicitudes que cumplen con los filtros de maquinaria/operador
            request_ids = None
            
            # Si hay filtros de maquinaria u operador, los aplicamos primero
            if machinery_id is not None or operator_id is not None:
                machinery_users = RequestMachineryUser.objects.all()
                
                if machinery_id is not None:
                    machinery_users = machinery_users.filter(machinery_id=machinery_id)
                if operator_id is not None:
                    machinery_users = machinery_users.filter(user_id=operator_id)
                
                # Obtener IDs únicos de solicitudes que cumplen con los filtros
                request_ids = machinery_users.values_list('request_id', flat=True).distinct()
            
            # Construir consulta de solicitudes
            queryset = ServiceRequest.objects.filter(
                request_status_id__in=[20, 21, 22]  # Solo estados 20, 21, 22
            )
            
            # Aplicar filtro de IDs de solicitud si es necesario
            if request_ids is not None:
                queryset = queryset.filter(id_request__in=request_ids)
            
            # Aplicar filtros adicionales
            if status_filter:
                queryset = queryset.filter(request_status_id=status_filter)
                
            if customer_id:
                queryset = queryset.filter(customer_id=customer_id)
                
            if start_date:
                queryset = queryset.filter(scheduled_start_date__gte=start_date)
                
            if end_date:
                queryset = queryset.filter(scheduled_start_date__lte=end_date)
            
            # Ordenar por fecha programada descendente
            queryset = queryset.order_by('-scheduled_start_date')
            
            # Pasar los filtros al contexto para que el serializer los use
            context = {
                'request': request,
                'filters': {
                    'machinery_id': machinery_id,
                    'operator_id': operator_id
                }
            }
            
            # Serializar datos
            serializer = ServiceRequestMachineryDataSerializer(
                queryset,
                many=True,
                context=context
            )
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error al obtener solicitudes de servicio: {str(e)}")
            return Response(
                {"error": "Error al obtener las solicitudes de servicio"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=True, methods=['get'])
    def by_request(self, request, pk=None):
        """
        Obtiene los datos de telemetría para una solicitud específica.
        Requiere el permiso con ID 172.
        
        Parámetros opcionales:
        - start_date: Fecha de inicio en formato ISO 8601 (ej: 2025-01-01T00:00:00)
        - end_date: Fecha de fin en formato ISO 8601 (ej: 2025-01-31T23:59:59)
        - machinery_id: ID de la maquinaria específica a filtrar (opcional)
        - operator_id: ID del operador para filtrar maquinarias (opcional)
        
        Se pueden combinar los filtros de la siguiente manera:
        - Solo machinery_id: Trae solo la maquinaria especificada
        - Solo operator_id: Trae todas las maquinarias operadas por ese usuario
        - Ambos: Trae la maquinaria especificada solo si es operada por el usuario especificado
        """
        try:
            logger.info(f"Iniciando solicitud de datos para request_id: {pk}")
            
            # Obtener parámetros de filtro
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            machinery_id = request.query_params.get('machinery_id')
            operator_id = request.query_params.get('operator_id')
            
            # Convertir a enteros si existen
            if machinery_id is not None:
                try:
                    machinery_id = int(machinery_id)
                except (ValueError, TypeError):
                    return Response(
                        {"detail": "El parámetro machinery_id debe ser un número entero"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            if operator_id is not None:
                try:
                    operator_id = int(operator_id)
                except (ValueError, TypeError):
                    return Response(
                        {"detail": "El parámetro operator_id debe ser un número entero"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            logger.debug(f"Filtros - start_date: {start_date}, end_date: {end_date}, "
                        f"machinery_id: {machinery_id}, operator_id: {operator_id}")
            
            # Validar que end_date no sea anterior a start_date
            if start_date and end_date:
                from django.utils.dateparse import parse_datetime
                try:
                    start = parse_datetime(start_date)
                    end = parse_datetime(end_date)
                    if start and end and end < start:
                        return Response(
                            {"detail": "La fecha de fin no puede ser anterior a la fecha de inicio"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error al analizar fechas: {str(e)}")
                    return Response(
                        {"detail": "Formato de fecha inválido. Use el formato ISO 8601 (ej: 2025-01-01T00:00:00)"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Verificar permiso
            logger.debug("Verificando permisos...")
            if not self.check_permission(request, 172):
                logger.warning(f"Acceso denegado para el usuario: {request.user}")
                return Response(
                    {"detail": "No tiene permiso para acceder al historial de los datos de la solicitud"}, 
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
            
            # Obtener los datos de la maquinaria con los filtros aplicados
            result = get_machinery_data(
                request_id=pk,
                request=request,
                start_date=start_date,
                end_date=end_date,
                machinery_id=machinery_id,
                operator_id=operator_id
            )
            
            logger.debug(f"Datos de maquinaria obtenidos: {len(result)} registros")
            
            # Serializar y retornar los datos
            serializer = DataSerializer(
                result, 
                many=True,
                context={
                    'request': request,
                    'start_date': start_date,
                    'end_date': end_date,
                    'machinery_id': machinery_id,
                    'operator_id': operator_id
                }
            )
            
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
