import os
import logging
import requests
from rest_framework import serializers

logger = logging.getLogger(__name__)
from monitoring.models.data import Data
from service_requests.models.request_machinery_user import RequestMachineryUser
from machinery.models.machinery import Machinery
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.obd_faults import OBD_Faults

class DataSerializer(serializers.Serializer):
    machinery_name = serializers.CharField()
    serial_number = serializers.CharField()
    id_user = serializers.IntegerField()
    user_name = serializers.SerializerMethodField()
    id_device = serializers.IntegerField()
    imei = serializers.CharField()
    operating_time_hours = serializers.FloatField()
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

def get_machinery_data(request_id, request=None, start_date=None, end_date=None):
    """
    Obtiene los datos de maquinaria para una solicitud específica con filtros de fecha opcionales.
    
    Args:
        request_id: ID de la solicitud
        request: Objeto request para el contexto de autenticación
        start_date: Fecha de inicio para filtrar los datos (opcional)
        end_date: Fecha de fin para filtrar los datos (opcional)
    """
    # Get all machinery assigned to this request with their users
    request_machinery = RequestMachineryUser.objects.filter(request_id=request_id).select_related(
        'machinery',
        'user',
        'machinery__id_device'
    )
    
    # Convertir fechas de string a datetime si vienen como parámetros
    if isinstance(start_date, str):
        from django.utils.dateparse import parse_datetime
        start_date = parse_datetime(start_date)
    if isinstance(end_date, str):
        from django.utils.dateparse import parse_datetime
        end_date = parse_datetime(end_date)
    
    result = []
    
    for rm in request_machinery:
        machinery = rm.machinery
        if not machinery.id_device:
            continue
            
        # Build base query for data points
        data_points_query = Data.objects.filter(
            id_device=machinery.id_device,
            id_request=request_id
        )
        
        # Aplicar filtros de fecha si están presentes
        if start_date:
            data_points_query = data_points_query.filter(registered_at__gte=start_date)
        if end_date:
            data_points_query = data_points_query.filter(registered_at__lte=end_date)
            
        # Ejecutar la consulta con ordenamiento
        data_points = data_points_query.select_related('id_parameter').order_by('registered_at')
        
        # Calculate operating time (time between first and last data point within the filtered range)
        operating_time_hours = 0
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
        
        machine_data = {
            'machinery_name': machinery.machinery_name,
            'serial_number': machinery.serial_number,
            'id_user': rm.user.id_user,
            'id_device': machinery.id_device.id_device,
            'imei': machinery.id_device.IMEI,
            'operating_time_hours': operating_time_hours,
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
