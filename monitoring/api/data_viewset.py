import logging
from datetime import datetime, time
from django.utils import timezone
from django.db.models import Q, Avg, Sum, Min, Max
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from service_requests.models.service_request import ServiceRequest
from service_requests.models.request_machinery_user import RequestMachineryUser
from monitoring.serializers.data_serializer import DataSerializer, get_machinery_data
from monitoring.serializers.service_request_machinery_serializer import ServiceRequestMachineryDataSerializer
from monitoring.models.data import Data

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
        - start_date: Fecha de inicio (formatos aceptados: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
        - end_date: Fecha de fin (formatos aceptados: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
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
                    {"error": "No tiene permiso para acceder a este recurso"},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Obtener parámetros de consulta
            status_filter = request.query_params.get('status', None)
            customer_id = request.query_params.get('customer_id', None)
            start_datetime_str = request.query_params.get('start_date', None)
            end_datetime_str = request.query_params.get('end_date', None)
            machinery_id = request.query_params.get('machinery_id', None)
            operator_id = request.query_params.get('operator_id', None)
            
            # Variables para fechas
            start_date = None
            end_date = None
            start_datetime = None
            end_datetime = None
            
            # Parsear fechas/horas
            if start_datetime_str:
                try:
                    if 'T' in start_datetime_str:
                        naive_start = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M:%S')
                        start_datetime = timezone.make_aware(naive_start, timezone.get_current_timezone())
                        start_date = start_datetime.date()
                    else:
                        start_date = datetime.strptime(start_datetime_str, '%Y-%m-%d').date()
                        # Si solo es fecha, establecer la hora a 00:00:00 en la zona horaria actual
                        start_datetime = timezone.make_aware(
                            datetime.combine(start_date, time.min),
                            timezone.get_current_timezone()
                        )
                except ValueError:
                    return Response(
                        {"error": "Formato de fecha/hora de inicio inválido. Use YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            if end_datetime_str:
                try:
                    if 'T' in end_datetime_str:
                        naive_end = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M:%S')
                        end_datetime = timezone.make_aware(naive_end, timezone.get_current_timezone())
                        end_date = end_datetime.date()
                    else:
                        end_date = datetime.strptime(end_datetime_str, '%Y-%m-%d').date()
                        # Si solo es fecha, establecer la hora a 23:59:59.999999 en la zona horaria actual
                        end_of_day = datetime.combine(end_date, time.max)
                        end_datetime = timezone.make_aware(
                            end_of_day,
                            timezone.get_current_timezone()
                        )
                except ValueError:
                    return Response(
                        {"error": "Formato de fecha/hora de fin inválido. Use YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
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
            
            # Obtener los IDs de solicitudes que tienen datos en el rango de fechas
            data_queryset = Data.objects.all()
            
            # Aplicar filtros de maquinaria y operador si existen
            if machinery_id is not None:
                data_queryset = data_queryset.filter(id_machinery=machinery_id)
            if operator_id is not None:
                data_queryset = data_queryset.filter(id_user=operator_id)
                
            # Aplicar filtros de fechas
            if start_datetime:
                data_queryset = data_queryset.filter(registered_at__gte=start_datetime)
            if end_datetime:
                data_queryset = data_queryset.filter(registered_at__lte=end_datetime)
                
            # Obtener fechas mínima y máxima si no se proporcionaron
            if not start_datetime or not end_datetime:
                date_range = data_queryset.aggregate(
                    min_date=Min('registered_at'),
                    max_date=Max('registered_at')
                )
                if date_range['min_date'] and date_range['max_date']:
                    if not start_datetime:
                        start_datetime = date_range['min_date']
                    if not end_datetime:
                        end_datetime = date_range['max_date']
            
            # Obtener IDs únicos de solicitudes que tienen datos en el rango
            request_ids_from_data = data_queryset.exclude(
                id_request__isnull=True
            ).values_list('id_request', flat=True).distinct()
            
            # Construir consulta de solicitudes
            queryset = ServiceRequest.objects.filter(
                request_status_id__in=[20, 21, 22],  # Solo estados 20, 21, 22
                id_request__in=request_ids_from_data
            )
            
            # Aplicar filtro de IDs de solicitud si se proporcionaron
            if request_ids is not None:
                queryset = queryset.filter(id_request__in=request_ids)
            
            # Validar que la fecha de fin no sea menor que la de inicio
            if start_date and end_date and end_date < start_date:
                return Response(
                    {"error": "La fecha de fin no puede ser anterior a la fecha de inicio"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Aplicar filtros adicionales
            if status_filter:
                queryset = queryset.filter(request_status_id=status_filter)
                
            if customer_id:
                queryset = queryset.filter(customer_id=customer_id)
            
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
            
            # Preparar la respuesta con las fechas al principio si no se proporcionaron en la consulta
            response_data = {}
            
            # Agregar fechas al inicio si no se proporcionaron en la consulta
            if not start_datetime_str and start_datetime:
                response_data["start_date"] = start_datetime.strftime('%Y-%m-%dT%H:%M:%S')
            if not end_datetime_str and end_datetime:
                response_data["end_date"] = end_datetime.strftime('%Y-%m-%dT%H:%M:%S')
                
            # Agregar los datos de las solicitudes
            response_data["requests"] = serializer.data
            
            # Si hay filtro de maquinaria, agregar información resumida
            if machinery_id is not None:
                # Si no hay request_ids (no se filtró por operador), obtener todos los request_ids del queryset
                if request_ids is None:
                    request_ids = queryset.values_list('id_request', flat=True).distinct()
                
                # Obtener datos de la maquinaria, pasando también el operador y los request_ids si están presentes
                machinery_data = self._get_machinery_summary(
                    machinery_id=machinery_id,
                    start_date=start_date,
                    end_date=end_date,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    operator_id=operator_id,
                    request_ids=request_ids
                )
                
                if machinery_data:
                    # Calcular effective_working_hours sumando los valores individuales de las solicitudes
                    # Mantener los valores separados por maquinaria
                    effective_hours_by_machinery = {}
                    
                    for request in response_data.get('requests', []):
                        if 'effective_working_hours' in request:
                            hours_str = request['effective_working_hours']
                            if isinstance(hours_str, str):
                                # Separar los valores por ';' y procesar cada uno
                                hours_values = hours_str.split(';')
                                for i, value in enumerate(hours_values):
                                    try:
                                        hours = float(value.strip().split('h')[0].strip())
                                        if i not in effective_hours_by_machinery:
                                            effective_hours_by_machinery[i] = 0.0
                                        effective_hours_by_machinery[i] += hours
                                    except (ValueError, AttributeError, IndexError) as e:
                                        print(f"Error al procesar effective_working_hours: {e}")
                    
                    # Formatear los resultados sumados por maquinaria
                    if effective_hours_by_machinery:
                        total_effective_hours = "; ".join([f"{hours:.2f} h" for i, hours in sorted(effective_hours_by_machinery.items())])
                        machinery_data['effective_working_hours'] = total_effective_hours
                    else:
                        machinery_data['effective_working_hours'] = "0.00 h"
                    
                    # Calcular operating_time_hours sumando los valores individuales de las solicitudes
                    operating_hours_by_machinery = {}
                    
                    for request in response_data.get('requests', []):
                        if 'operating_time_hours' in request:
                            hours_str = request['operating_time_hours']
                            if isinstance(hours_str, str):
                                # Separar los valores por ';' y procesar cada uno
                                hours_values = hours_str.split(';')
                                for i, value in enumerate(hours_values):
                                    try:
                                        hours = float(value.strip().split('h')[0].strip())
                                        if i not in operating_hours_by_machinery:
                                            operating_hours_by_machinery[i] = 0.0
                                        operating_hours_by_machinery[i] += hours
                                    except (ValueError, AttributeError, IndexError) as e:
                                        print(f"Error al procesar operating_time_hours: {e}")
                    
                    # Formatear los resultados sumados por maquinaria
                    if operating_hours_by_machinery:
                        total_operating_hours = "; ".join([f"{hours:.2f} h" for i, hours in sorted(operating_hours_by_machinery.items())])
                        machinery_data['operating_time_hours'] = total_operating_hours
                    else:
                        machinery_data['operating_time_hours'] = "0.00 h"
                    
                    response_data = {**machinery_data, **response_data}
            
            return Response(response_data)
            
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
    def _get_machinery_summary(self, machinery_id, start_date=None, end_date=None, start_datetime=None, end_datetime=None, operator_id=None, request_ids=None):
        """
        Obtiene un resumen de las estadísticas de la maquinaria.
        Nota: operating_time_hours y effective_working_hours ahora se calculan sumando los valores individuales de las solicitudes.
        
        Args:
            machinery_id: ID de la maquinaria
            start_date: Fecha de inicio (solo fecha)
            end_date: Fecha de fin (solo fecha)
            start_datetime: Fecha y hora de inicio (datetime)
            end_datetime: Fecha y hora de fin (datetime)
            operator_id: ID del operador (opcional)
            request_ids: Lista de IDs de solicitudes (opcional)
        """
        try:
            # Filtrar por maquinaria, operador (si se proporciona) y rango de fechas
            filters = Q(id_machinery=machinery_id)
            
            # Si se proporciona operator_id, filtrar por ese operador
            if operator_id is not None:
                filters &= Q(id_user=operator_id)
            
            # Si se proporcionan request_ids, filtrar por esas solicitudes
            if request_ids is not None and request_ids.exists():
                filters &= Q(id_request__in=request_ids)
            
            # Aplicar filtros de fecha/hora
            if start_datetime and end_datetime:
                # Usar filtro de rango de fechas/horas exactas
                filters &= Q(registered_at__range=(start_datetime, end_datetime))
            else:
                # Usar filtros de fecha (compatibilidad con versiones anteriores)
                if start_date:
                    filters &= Q(registered_at__date__gte=start_date)
                if end_date:
                    filters &= Q(registered_at__date__lte=end_date)
            
            # Obtener datos de la maquinaria con los filtros aplicados
            data = Data.objects.filter(filters)
            
            # Si no hay datos, retornar valores por defecto
            if not data.exists():
                return {
                    "operating_time_hours": 0,
                    "total_distance_km": 0,
                    "effective_working_hours": 0,
                    "average_speed": 0,
                    "average_consumption": 0
                }
            
            # Calcular promedios de velocidad (parámetro 3) y consumo (parámetro 12)
            avg_speed = data.filter(id_parameter=3).aggregate(avg=Avg('data'))['avg'] or 0
            avg_consumption = data.filter(id_parameter=12).aggregate(avg=Avg('data'))['avg'] or 0
            
            # Calcular distancia total (parámetro 15) con los mismos filtros
            distance_data = data.filter(id_parameter=15).order_by('registered_at')
            total_distance_meters = 0
            
            if distance_data.exists():
                # Obtener todos los puntos de distancia con sus valores y fechas
                points = list(distance_data.values('data', 'registered_at'))
                
                # Encontrar segmentos entre ceros
                segments = []
                current_segment = []
                
                for point in points:
                    if point['data'] == 0 and current_segment:
                        # Si encontramos un 0 y hay un segmento en progreso, lo guardamos
                        segments.append(current_segment)
                        current_segment = []
                    elif point['data'] > 0:
                        # Solo agregar puntos con datos mayores a 0
                        current_segment.append(point)
                
                # Agregar el último segmento si existe
                if current_segment:
                    segments.append(current_segment)
                
                # Calcular la distancia total sumando el valor máximo de cada segmento
                for segment in segments:
                    if segment:  # Asegurarse de que el segmento no esté vacío
                        # Obtener el valor máximo del segmento
                        max_in_segment = max(segment, key=lambda x: x['data'])
                        total_distance_meters += max_in_segment['data']
                
                # Si no hay segmentos pero hay datos positivos (ej: un solo valor sin ceros)
                if not segments and any(p['data'] > 0 for p in points):
                    last_non_zero = next((p['data'] for p in reversed(points) if p['data'] > 0), 0)
                    total_distance_meters = last_non_zero
            
            # Convertir a kilómetros y redondear a 3 decimales
            total_distance = round(total_distance_meters / 1000, 3) if total_distance_meters > 0 else 0
            
            # Los valores de operating_time_hours y effective_working_hours se calcularán sumando los valores individuales
            # de las solicitudes en el método service_requests
            
            return {
                "operating_time_hours": f"{0:.2f} h",  # Se sobrescribirá en service_requests
                "total_distance_km": f"{round(total_distance, 3)} km",
                "effective_working_hours": f"{0:.2f} h",  # Se sobrescribirá en service_requests
                "average_speed": f"{round(avg_speed, 2)} km/h",
                "average_consumption": f"{round(avg_consumption, 2)} L/h"
            }
            
        except Exception as e:
            logger.error(f"Error al obtener resumen de maquinaria: {str(e)}")
            return {}
    
    def list(self, request):
        return Response(
            {"detail": "Por favor proporcione un ID de solicitud usando la acción 'by_request'"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
