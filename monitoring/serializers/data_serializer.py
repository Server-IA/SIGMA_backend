import os
import logging
import requests
from django.db.models import Q
from rest_framework import serializers

logger = logging.getLogger(__name__)
from monitoring.models.data import Data
from service_requests.models.request_machinery_user import RequestMachineryUser
from machinery.models.machinery import Machinery
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.obd_faults import OBD_Faults

class DataSerializer(serializers.Serializer):
    id_machinery = serializers.IntegerField()
    machinery_name = serializers.CharField()
    serial_number = serializers.CharField()
    id_user = serializers.IntegerField()
    user_name = serializers.SerializerMethodField()
    id_device = serializers.IntegerField()
    IMEI = serializers.CharField()
    operating_time_hours = serializers.FloatField()
    total_distance_km = serializers.FloatField()
    effective_working_hours = serializers.FloatField()
    parameters = serializers.ListField(child=serializers.DictField())
    
    def _get_external_user(self, user_id: int) -> dict:
        """Obtiene la info básica del usuario desde el servicio externo.
        Retorna {} si no hay info o en caso de error.
        """
        if not user_id:
            return {}

        # Usar un diccionario de caché por user_id
        cache_key = f'_ext_user_cache_{user_id}'
        cached = getattr(self, cache_key, None)
        if cached is not None:
            return cached

        # Inicializar el caché si no existe
        if not hasattr(self, '_ext_users_cache'):
            self._ext_users_cache = {}

        if user_id in self._ext_users_cache:
            return self._ext_users_cache[user_id]

        base_url = os.getenv("AUTH_SERVICE_URL", "").rstrip("/")
        if not base_url:
            logger.warning("AUTH_SERVICE_URL no está configurado")
            return {}

        url = f"{base_url}/users/users/basic-user-list/by-ids"
        headers = {}
        
        # Obtener el token de autenticación del contexto
        request = self.context.get("request") if hasattr(self, 'context') and self.context else None
        if request is not None:
            # Intentar obtener el header de autorización de diferentes ubicaciones
            auth_header = (
                getattr(request, "META", {}).get("HTTP_AUTHORIZATION") or 
                (request.headers.get("Authorization") if hasattr(request, "headers") else None)
            )
            if auth_header:
                headers["Authorization"] = auth_header
            else:
                logger.warning("No se encontró el token de autenticación en la solicitud")
        else:
            logger.warning("No se pudo obtener el objeto request del contexto")

        try:
            resp = requests.post(
                url,
                json={"ids": [user_id]},
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                payload = resp.json() or {}
                data = payload.get("data") or []
                if isinstance(data, list) and data:
                    user_data = data[0]
                    # Guardar en caché para futuras consultas
                    self._ext_users_cache[user_id] = user_data
                    setattr(self, cache_key, user_data)
                    return user_data
            else:
                logger.error(f"Error al obtener datos del usuario {user_id}: {resp.status_code} - {resp.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la solicitud al servicio de autenticación: {str(e)}")
            
        return {}
        
    def get_user_name(self, obj):
        try:
            user_id = obj.get('id_user')
            if not user_id:
                return None
                
            # Obtener datos del usuario desde el servicio externo
            user_data = self._get_external_user(user_id)
            
            if user_data:
                name = user_data.get("name", "")
                first_last_name = user_data.get("first_last_name", "")
                second_last_name = user_data.get("second_last_name", "")
                return " ".join(filter(None, [name, first_last_name, second_last_name]))
                
        except Exception as e:
            logger.error(f"Error en get_user_name: {str(e)}")
            
        return None

def get_machinery_data(request_id, request=None, start_date=None, end_date=None, machinery_id=None, operator_id=None):
    """
    Obtiene los datos de maquinaria para una solicitud específica con filtros opcionales.
    
    Args:
        request_id: ID de la solicitud
        request: Objeto request para el contexto de autenticación
        start_date: Fecha de inicio para filtrar los datos (opcional)
        end_date: Fecha de fin para filtrar los datos (opcional)
        machinery_id: ID de la maquinaria específica a filtrar (opcional)
        operator_id: ID del operador para filtrar maquinarias (opcional)
    """
    from django.db.models import Max
    
    # Convertir fechas de string a datetime si vienen como parámetros
    if isinstance(start_date, str):
        from django.utils.dateparse import parse_datetime
        start_date = parse_datetime(start_date)
    if isinstance(end_date, str):
        from django.utils.dateparse import parse_datetime
        end_date = parse_datetime(end_date)
    
    # Obtener todos los datos de la solicitud
    data_query = Data.objects.filter(id_request=request_id)
    
    # Aplicar filtro de maquinaria si se especifica
    if machinery_id is not None:
        data_query = data_query.filter(id_machinery=machinery_id)
    
    # Aplicar filtro de operador si se especifica
    if operator_id is not None:
        data_query = data_query.filter(id_user=operator_id)
    
    # Si no hay datos después de aplicar los filtros, retornar lista vacía
    if not data_query.exists():
        logger.warning(f"No se encontraron datos para los filtros: request_id={request_id}, "
                     f"machinery_id={machinery_id}, operator_id={operator_id}")
        return []
    
    # Obtener las maquinarias únicas con sus relaciones
    from django.db.models import F
    
    machinery_data = data_query.select_related(
        'id_machinery',
        'id_device',  # Relación directa con TelemetryDevices
        'id_user'
    ).annotate(
        device_id=F('id_device__id_device'),  # Acceso directo al dispositivo
        IMEI=F('id_device__IMEI'),           # IMEI directo del dispositivo (mayúsculas para consistencia)
        machinery_name=F('id_machinery__machinery_name'),
        serial_number=F('id_machinery__serial_number'),
        user_id=F('id_user')
    ).values(
        'id_machinery',
        'machinery_name',
        'serial_number',
        'device_id',
        'IMEI',  # Cambiado a mayúsculas para consistencia con el nombre en el modelo
        'user_id'
    ).distinct()
    
    # Aplicar filtros de fecha si están presentes
    if start_date:
        data_query = data_query.filter(registered_at__gte=start_date)
    if end_date:
        data_query = data_query.filter(registered_at__lte=end_date)
    
    # Obtener el último registro por maquinaria para tener la información más reciente
    latest_data = data_query.values('id_machinery').annotate(
        latest_registered=Max('registered_at')
    )
    
    # Obtener los datos completos de los registros más recientes
    latest_records = []
    for item in latest_data:
        latest_record = data_query.filter(
            id_machinery=item['id_machinery'],
            registered_at=item['latest_registered']
        ).select_related('id_machinery', 'id_device').first()
        if latest_record:
            latest_records.append(latest_record)
    
    result = []
    
    for record in machinery_data:
        machinery = record['id_machinery']
        
        # Obtener datos para esta maquinaria
        data_points_query = data_query.filter(
            id_machinery=machinery
        ).select_related('id_parameter', 'id_machinery', 'id_device')
        
        # Ordenar por fecha
        data_points = data_points_query.order_by('registered_at')
        
        # Aplicar filtros de fecha si están presentes
        if start_date:
            data_points_query = data_points_query.filter(registered_at__gte=start_date)
        if end_date:
            data_points_query = data_points_query.filter(registered_at__lte=end_date)
            
        # Ejecutar la consulta con ordenamiento
        data_points = data_points_query.select_related('id_parameter').order_by('registered_at')
        
        # Calculate operating time (time between first and last data point within the filtered range)
        operating_time_hours = 0
        effective_working_hours = 0
        
        if data_points.exists():
            first_point = data_points.first()
            last_point = data_points.last()
            
            # Siempre usamos las fechas de los datos reales, no las del filtro
            # para que el tiempo de operación refleje solo el tiempo con datos
            time_diff = last_point.registered_at - first_point.registered_at
            
            # Si hay un solo punto de datos, asumimos 1 minuto de operación
            # para evitar que sea cero cuando hay datos
            if data_points.count() == 1:
                operating_time_hours = round(60 / 3600, 2)  # 1 minuto en horas
            else:
                operating_time_hours = max(0, round(time_diff.total_seconds() / 3600, 2))
            
            # Calcular effective_working_hours (tiempo donde id_parameter=18 y data=2)
            working_periods = []
            current_start = None
            
            # Obtener los datos del parámetro 18
            working_data = data_points.filter(id_parameter_id=18).order_by('registered_at')
            
            for i, point in enumerate(working_data):
                # Si encontramos un punto con data=2
                if point.data == 2:
                    # Si es el inicio de un nuevo período de trabajo
                    if current_start is None:
                        current_start = point.registered_at
                # Si encontramos un punto que no es 2 y teníamos un período abierto
                elif current_start is not None:
                    # Si no es el último punto, usamos el punto anterior
                    if i > 0 and working_data[i-1].data == 2:
                        working_periods.append({
                            'start': current_start,
                            'end': working_data[i-1].registered_at
                        })
                    current_start = None
            
            # Cerrar el último período si es necesario
            if current_start is not None and working_data.last().data == 2:
                working_periods.append({
                    'start': current_start,
                    'end': working_data.last().registered_at
                })
            
            # Sumar la duración de todos los períodos de trabajo
            for period in working_periods:
                duration = (period['end'] - period['start']).total_seconds()
                effective_working_hours += max(0, duration) / 3600  # Convertir a horas
            
            # Redondear a 2 decimales
            effective_working_hours = round(effective_working_hours, 2)
        
        # Organize data by parameter
        parameters_data = {}
        for data in data_points:
            param_id = data.id_parameter.id
            if param_id not in parameters_data:
                parameters_data[param_id] = {
                    'parameter_id': param_id,
                    'parameter_name': data.id_parameter.parameter_name,
                    'unit': data.id_parameter.unit,
                    'data_points': [],
                    'statistics': {
                        'max_value': None,
                        'min_value': None,
                        'average': None
                    }
                }
            
            # Store numeric values for statistics calculation
            if data.data is not None:
                if (parameters_data[param_id]['statistics']['max_value'] is None or 
                    data.data > parameters_data[param_id]['statistics']['max_value']):
                    parameters_data[param_id]['statistics']['max_value'] = float(data.data)
                    
                if (parameters_data[param_id]['statistics']['min_value'] is None or 
                    data.data < parameters_data[param_id]['statistics']['min_value']):
                    parameters_data[param_id]['statistics']['min_value'] = float(data.data)
            
            # Get OBD fault name if exists
            obd_fault_name = None
            if data.obd_fault:
                try:
                    fault = OBD_Faults.objects.get(code=data.obd_fault)
                    obd_fault_name = fault.description
                except OBD_Faults.DoesNotExist:
                    obd_fault_name = None
            
            parameters_data[param_id]['data_points'].append({
                'id': data.id_data,
                'data': data.data,
                'registered_at': data.registered_at,
                'obd_fault': data.obd_fault,
                'obd_fault_name': obd_fault_name,
                'alert': data.alert
            })
        
        # Calculate averages and convert dict to list
        parameters_list = []
        for param_data in parameters_data.values():
            if param_data['data_points']:
                # Calculate average
                values = [dp['data'] for dp in param_data['data_points'] if dp['data'] is not None]
                if values:
                    param_data['statistics']['average'] = sum(values) / len(values)
                    
                    # Convert to float for JSON serialization
                    param_data['statistics']['max_value'] = float(param_data['statistics']['max_value'])
                    param_data['statistics']['min_value'] = float(param_data['statistics']['min_value'])
                else:
                    param_data['statistics'] = None
            else:
                param_data['statistics'] = None
                
            parameters_list.append(param_data)
        
        # Obtener el ID de usuario del registro de datos
        user_id = record['user_id']
        
        # Calcular la distancia total recorrida (parámetro 15)
        total_distance_meters = 0
        distance_parameter_data = None
        
        # Buscar los datos del parámetro de distancia (id_parameter=15)
        for param_data in parameters_list:
            if param_data['parameter_id'] == 15:  # ID del parámetro de distancia
                distance_parameter_data = param_data
                break
        
        if distance_parameter_data and distance_parameter_data['data_points']:
            # Ordenar los puntos de datos por fecha para asegurar el orden correcto
            data_points = sorted(distance_parameter_data['data_points'], key=lambda x: x['registered_at'])
            
            # Encontrar los segmentos entre ceros
            segments = []
            current_segment = []
            
            for point in data_points:
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
            for i, segment in enumerate(segments, 1):
                if segment:  # Asegurarse de que el segmento no esté vacío
                    # Obtener el valor máximo del segmento
                    max_in_segment = max(segment, key=lambda x: x['data'])
                    total_distance_meters += max_in_segment['data']
            
            # Si no hay segmentos (todos los datos son 0 o no hay datos)
            if not segments and any(dp['data'] is not None and dp['data'] > 0 for dp in data_points):
                # Si hay datos pero no segmentos (por ejemplo, un solo valor sin ceros)
                last_non_zero = next((dp['data'] for dp in reversed(data_points) if dp['data'] is not None and dp['data'] > 0), 0)
                total_distance_meters = last_non_zero
        
        # Convertir a kilómetros
        total_distance_km = round(total_distance_meters / 1000, 6) if total_distance_meters is not None else 0
        
        machine_data = {
            'id_machinery': record['id_machinery'],
            'machinery_name': record['machinery_name'],
            'serial_number': record['serial_number'],
            'id_user': user_id,
            'id_device': record['device_id'],
            'IMEI': record['IMEI'],
            'operating_time_hours': operating_time_hours,
            'effective_working_hours': effective_working_hours,
            'total_distance_km': total_distance_km,
            'parameters': parameters_list
        }
        
        # Create serializer with request context and date range info
        serializer_context = {
            'start_date': start_date,
            'end_date': end_date
        }
        if request is not None:
            serializer_context['request'] = request
            
        serializer = DataSerializer(data=machine_data, context=serializer_context)
        if serializer.is_valid():
            result.append(serializer.data)
        else:
            # If serialization fails, log the error and return data without user_name
            logger.warning(f"Error en la serialización: {serializer.errors}")
            result.append(machine_data)
    
    return result
