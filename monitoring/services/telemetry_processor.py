"""
Procesador de telemetría en tiempo real
Integra el simulador con el sistema de monitoreo y validación
"""
import asyncio
import json
import logging
import math
import os
import re
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Optional, List, Tuple, Any
from decimal import Decimal

import websockets
import aiohttp
import requests
from django.db import transaction, connection
from django.utils import timezone as django_timezone
from django.core.exceptions import ObjectDoesNotExist

from machinery.models import (
    Machinery,
    TelemetryDevices,
    Parameters,
    ToleranceThresholds,
    TelemetryDeviceParameter,
    OBD_Faults,
    OBDFaultMachinery,
    EventTypes,
    EventTypeMachinery
)
from service_requests.models import ServiceRequest, RequestLocation, RequestMachineryUser
from monitoring.models import Data

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelemetryProcessor:
    """
    Procesador principal que escucha el WebSocket del simulador y procesa
    los datos según el flujo completo especificado.
    """
    
    # Cache para solicitudes activas (se actualiza diariamente)
    _active_requests_cache: Optional[Dict] = None
    _cache_date: Optional[date] = None
    
    # Cache para alertas consecutivas (evita notificar múltiples veces)
    _alert_cache: Dict[Tuple[int, int], int] = {}  # {(machinery_id, parameter_id): count}
    
    # Cache de paquetes procesados recientemente (evita procesamiento duplicado)
    _processed_packets_cache: Dict[str, datetime] = {}  # {imei_timestamp: processed_time}
    
    # Mapeo de IDs de parámetros AVL a nombres de campos
    PARAMETER_MAPPING = {
        239: 'ignition_status',  # Estado de Ignición
        240: 'movement_status',  # Estado de Movimiento
        24: 'speed',  # Velocidad
        387: 'gps_location',  # GPS
        21: 'gsm_signal',  # Señal GSM
        36: 'rpm',  # RPM
        32: 'engine_temp',  # Temperatura Motor
        31: 'engine_load',  # Carga Motor
        1159: 'oil_level',  # Nivel Aceite
        48: 'fuel_level',  # Nivel Combustible
        12: 'fuel_used_gps',  # Combustible Usado GPS
        60: 'instant_consumption',  # Consumo Instantáneo
        16: 'odometer_total',  # Odómetro Total
        199: 'odometer_trip',  # Odómetro Viaje
        253: 'event_type',  # Tipo Evento
        254: 'event_g_value',  # Valor G Evento
    }
    
    def __init__(self, simulator_url: str = "ws://simulator:8010/ws/telemetria"):
        """
        Inicializa el procesador
        
        Args:
            simulator_url: URL del WebSocket del simulador (sin parámetros)
        """
        # Obtener contraseña desde variable de entorno
        websocket_password = os.getenv("WEBSOCKET_PASSWORD")
        
        if not websocket_password:
            raise ValueError("WEBSOCKET_PASSWORD no está configurada en las variables de entorno")
        
        # Agregar parámetros processor=true y password
        if "?" in simulator_url:
            self.simulator_url = f"{simulator_url}&processor=true&password={websocket_password}"
        else:
            self.simulator_url = f"{simulator_url}?processor=true&password={websocket_password}"
        
        # URL del endpoint HTTP del simulador para reenviar paquetes procesados
        base_url = simulator_url.replace("ws://", "http://").replace("/ws/telemetria", "")
        self.simulator_http_url = base_url
        self.is_running = False
        # Refresco de solicitudes activas cada N paquetes
        self._active_requests_refresh_every = 4
        self._packets_since_refresh = 0
        
    def validate_tables_exist(self) -> bool:
        """
        Valida que todas las tablas necesarias existan en la base de datos
        
        Returns:
            bool: True si todas las tablas existen, False si alguna falta
        """
        required_tables = [
            'machinery',
            'telemetry_devices',
            'parameters',
            'data',  # Tabla principal para almacenar telemetría
            'service_requests',
            'obd_faults'
        ]
        
        missing_tables = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            for table in required_tables:
                if table not in existing_tables:
                    missing_tables.append(table)
        
        if missing_tables:
            logger.warning(
                f"Advertencia: Las siguientes tablas no existen: {', '.join(missing_tables)}. "
                "El procesamiento continuará pero puede fallar al intentar acceder a estas tablas."
            )
            return False
        
        logger.info("Todas las tablas requeridas existen")
        return True
    
    def get_active_requests(self, target_date: date = None) -> Dict[str, ServiceRequest]:
        """
        Obtiene las solicitudes activas para una fecha específica.
        
        NUEVA LÓGICA:
        - Si la fecha está DENTRO del rango [scheduled_start_date, scheduled_end_date]: 
          valida estados 20 y 21
        - Si la fecha está FUERA del rango: solo valida estado 21
        
        Cachea el resultado para evitar consultas repetidas en el mismo día.
        
        Args:
            target_date: Fecha objetivo (por defecto, fecha actual)
            
        Returns:
            Dict con id_request como clave y ServiceRequest como valor
        """
        if target_date is None:
            target_date = django_timezone.now().date()
        
        # Verificar si el cache es válido y si corresponde refrescar por contador
        if (self._active_requests_cache is not None and 
            self._cache_date == target_date):
            if self._packets_since_refresh < self._active_requests_refresh_every:
                self._packets_since_refresh += 1
                return self._active_requests_cache
            # Si alcanzó el umbral, se refresca más abajo
        
        try:
            from django.db.models import Q

            # 1A. Estado 21 dentro del rango completo
            requests_21_in_range = ServiceRequest.objects.filter(
                request_status_id=21,
                scheduled_start_date__lte=target_date,
                scheduled_end_date__gte=target_date
            ).select_related('request_location')

            # 1B. Estado 20 solo válido el día de inicio
            requests_20_start_day = ServiceRequest.objects.filter(
                request_status_id=20,
                scheduled_start_date=target_date
            ).select_related('request_location')

            # Combinar válidos "en rango" según regla: 21 todo el rango; 20 solo día de inicio
            requests_in_range = requests_21_in_range.union(requests_20_start_day)

            # 2. Fuera del rango solo estado 21
            requests_out_range = ServiceRequest.objects.filter(
                Q(request_status_id=21) &
                (Q(scheduled_start_date__gt=target_date) | Q(scheduled_end_date__lt=target_date))
            ).select_related('request_location')

            # Combinar ambos conjuntos evitando duplicados
            all_requests = requests_in_range.union(requests_out_range)
            
            self._active_requests_cache = {
                req.id_request: req for req in all_requests
            }
            self._cache_date = target_date
            self._packets_since_refresh = 0
            
            in_range_count = len(list(requests_in_range))
            out_range_count = len(list(requests_out_range))
            
            logger.info(
                f"Cache actualizado: {len(self._active_requests_cache)} solicitudes activas para {target_date} "
                f"(Dentro: 21 en rango + 20 solo día inicio -> {in_range_count}, Fuera: 21 -> {out_range_count})"
            )
            
            return self._active_requests_cache
            
        except Exception as e:
            logger.error(f"Error al obtener solicitudes activas: {str(e)}")
            return {}
    
    def get_device_machinery(self, imei: str) -> Optional[Tuple[TelemetryDevices, Machinery]]:
        """
        Obtiene el dispositivo y la maquinaria asociada por IMEI
        
        Args:
            imei: IMEI del dispositivo (string de 15 dígitos)
            
        Returns:
            Tupla (TelemetryDevices, Machinery) o None si no se encuentra
        """
        try:
            imei_int = int(imei)
            device = TelemetryDevices.objects.select_related().get(IMEI=imei_int)
            machinery = Machinery.objects.get(id_device=device)
            return (device, machinery)
        except (TelemetryDevices.DoesNotExist, Machinery.DoesNotExist, ValueError) as e:
            logger.warning(f"Dispositivo con IMEI {imei} no encontrado: {str(e)}")
            return None
    
    def get_device_parameters(self, device: TelemetryDevices) -> List[Parameters]:
        """
        Obtiene los parámetros configurados para un dispositivo
        
        Args:
            device: Instancia de TelemetryDevices
            
        Returns:
            Lista de parámetros configurados
        """
        try:
            parameter_ids = TelemetryDeviceParameter.objects.filter(
                telemetry_device=device
            ).values_list('parameter_id', flat=True)
            
            return list(Parameters.objects.filter(id__in=parameter_ids))
        except Exception as e:
            logger.error(f"Error al obtener parámetros del dispositivo: {str(e)}")
            return []
    
    def _get_operator_name(self, user_id: int) -> Optional[str]:
        """
        Obtiene el nombre completo del operario desde el servicio externo de usuarios
        
        Args:
            user_id: ID del usuario (operario)
            
        Returns:
            Nombre completo del operario o None si no se puede obtener
        """
        if not user_id:
            return None
        
        try:
            base_url = os.getenv("AUTH_SERVICE_URL", "").rstrip("/")
            if not base_url:
                logger.warning("AUTH_SERVICE_URL no está configurado. No se puede obtener nombre del operario.")
                return None
            
            url = f"{base_url}/users/users/basic-user-list/by-ids"
            headers = {
                "Content-Type": "application/json"
            }
            
            # Intentar obtener token de servicio si está disponible
            service_token = os.getenv("SERVICE_AUTH_TOKEN")
            if service_token:
                headers["Authorization"] = f"Bearer {service_token}"
            
            response = requests.post(
                url,
                json={"ids": [user_id]},
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                payload = response.json() or {}
                data = payload.get("data") or []
                if isinstance(data, list) and data:
                    user_data = data[0]
                    name = user_data.get("name", "").strip()
                    first_last_name = user_data.get("first_last_name", "").strip()
                    second_last_name = user_data.get("second_last_name", "").strip()
                    full_name = " ".join(filter(None, [name, first_last_name, second_last_name]))
                    return full_name if full_name else None
            else:
                logger.warning(f"Error al obtener datos del operario {user_id}: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error de conexión al obtener nombre del operario {user_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al obtener nombre del operario {user_id}: {str(e)}")
            
        return None
    
    def calculate_logistic_status(
        self,
        gps_location: str,
        machinery: Machinery,
        active_requests: Dict[str, ServiceRequest]
    ) -> Optional[str]:
        """
        Calcula el estado logístico basado en la ubicación GPS y las solicitudes activas
        
        Args:
            gps_location: Coordenada GPS en formato ISO6709 (+DD.DDDDD-DDD.DDDDD/)
            machinery: Instancia de Machinery
            active_requests: Diccionario de solicitudes activas
            
        Returns:
            "Ida", "Vuelta", "Trabajo" o None
        """
        try:
            # Parsear coordenadas GPS (formato: +lat-lon/)
            match = re.match(r'\+([+-]?\d+\.?\d*)([+-]?\d+\.?\d*)/', gps_location)
            if not match:
                return None
            
            current_lat = float(match.group(1))
            current_lon = float(match.group(2))
            
            # Buscar solicitudes activas para esta maquinaria
            machinery_requests = []
            for req_id, req in active_requests.items():
                try:
                    # Verificar si la maquinaria está asignada a esta solicitud
                    RequestMachineryUser.objects.get(
                        request_id=req_id,
                        machinery=machinery
                    )
                    if hasattr(req, 'request_location') and req.request_location:
                        machinery_requests.append(req)
                except RequestMachineryUser.DoesNotExist:
                    continue
            
            if not machinery_requests:
                return None
            
            # Usar la primera solicitud encontrada para calcular distancia
            req = machinery_requests[0]
            if not hasattr(req, 'request_location') or not req.request_location:
                return None
            
            req_location = req.request_location
            req_lat = float(req_location.latitude)
            req_lon = float(req_location.longitude)
            
            # Calcular distancia usando fórmula de Haversine (km)
            distance = self._calculate_distance(
                current_lat, current_lon,
                req_lat, req_lon
            )
            
            # Definir umbrales (en km)
            WORK_RADIUS = 5.0  # Radio para considerar "en trabajo"
            GOING_RADIUS = 20.0  # Radio para considerar "en camino"
            
            if distance <= WORK_RADIUS:
                return "Trabajo"
            elif distance <= GOING_RADIUS:
                # Simplificado: considerar "Ida" si está acercándose
                # En producción, se podría usar historial de ubicaciones
                return "Ida"
            else:
                return "Vuelta"
                
        except Exception as e:
            logger.error(f"Error calculando estado logístico: {str(e)}")
            return None
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula la distancia entre dos puntos GPS usando fórmula de Haversine
        
        Returns:
            Distancia en kilómetros
        """
        R = 6371  # Radio de la Tierra en km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def check_thresholds(
        self,
        machinery: Machinery,
        parameter_name: str,
        value: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un valor supera los umbrales configurados
        
        Args:
            machinery: Instancia de Machinery
            parameter_name: Nombre del campo del parámetro
            value: Valor a verificar
            
        Returns:
            Tupla (is_alert, reason)
        """
        try:
            # Obtener el parámetro por nombre
            try:
                parameter = Parameters.objects.get(parameter_name=parameter_name)
            except Parameters.DoesNotExist:
                return (False, None)
            
            # Obtener umbrales para esta maquinaria y parámetro
            thresholds = ToleranceThresholds.objects.filter(
                id_machinery=machinery,
                id_parameter=parameter,
                alert_enabled=True
            ).first()
            
            if not thresholds:
                return (False, None)
            
            # Verificar umbrales
            is_alert = False
            reason = None
            
            if thresholds.minimum_threshold is not None and value < thresholds.minimum_threshold:
                is_alert = True
                reason = f"Valor {value} por debajo del mínimo {thresholds.minimum_threshold}"
            elif thresholds.maximum_threshold is not None and value > thresholds.maximum_threshold:
                is_alert = True
                reason = f"Valor {value} por encima del máximo {thresholds.maximum_threshold}"
            
            # Verificar si es primera vez consecutiva
            cache_key = (machinery.id_machinery, parameter.id)
            if is_alert:
                self._alert_cache[cache_key] = self._alert_cache.get(cache_key, 0) + 1
                is_first_time = self._alert_cache[cache_key] == 1
                
                if is_first_time:
                    # Primera vez → enviar notificación (aquí solo logueamos)
                    logger.warning(
                        f"ALERTA: {machinery.machinery_name} - "
                        f"Parámetro {parameter_name}: {reason}"
                    )
                    # TODO: Integrar sistema de notificaciones aquí
                    
                return (True, reason)
            else:
                # Resetear contador si el valor está dentro del rango
                if cache_key in self._alert_cache:
                    del self._alert_cache[cache_key]
                return (False, None)
                
        except Exception as e:
            logger.error(f"Error verificando umbrales: {str(e)}")
            return (False, None)

    def _get_event_type_config(self, machinery: Machinery) -> Dict[int, Dict[str, Optional[float]]]:
        """
        Retorna la configuración de tipos de evento por maquinaria:
        {id_event_type: {"alert_enabled": bool, "threshold": float|None}}
        """
        cfg: Dict[int, Dict[str, Optional[float]]] = {}
        try:
            rows = EventTypeMachinery.objects.filter(id_machinery=machinery)
            for row in rows:
                if row.id_event_type_id is not None:
                    cfg[int(row.id_event_type_id)] = {
                        "alert_enabled": bool(row.alert_enabled),
                        "threshold": row.threshold,
                    }
        except Exception as e:
            logger.error(f"Error obteniendo configuración de eventos: {str(e)}")
        return cfg

    def _get_obd_whitelist(self, machinery: Machinery) -> Dict[str, bool]:
        """
        Retorna whitelist de fallas OBD por maquinaria: {CODE: alert_enabled_bool}
        """
        wl: Dict[str, bool] = {}
        try:
            qs = OBDFaultMachinery.objects.filter(id_machinery=machinery).select_related('id_obd_fault')
            for row in qs:
                code = (row.id_obd_fault.code or "").upper()
                if code:
                    wl[code] = bool(row.alert_enabled)
        except Exception as e:
            logger.error(f"Error obteniendo whitelist OBD: {str(e)}")
        return wl

    def _event_permitted(
        self,
        event_type: Optional[int],
        g_value: Optional[float],
        cfg: Dict[int, Dict[str, Optional[float]]]
    ) -> bool:
        if event_type is None:
            return False
        c = cfg.get(int(event_type))
        if not c or not c.get("alert_enabled", False):
            return False
        thr = c.get("threshold")
        if thr is None:
            return True
        return g_value is not None and float(g_value) >= float(thr)
    
    def process_obd_faults(
        self,
        machinery: Machinery,
        fault_codes: List[str],
        timestamp: datetime
    ):
        """
        Procesa y almacena las fallas OBD activas
        
        Args:
            machinery: Instancia de Machinery
            fault_codes: Lista de códigos de fallas OBD
            timestamp: Timestamp de la telemetría
        """
        if not fault_codes:
            return
        
        try:
            whitelist = self._get_obd_whitelist(machinery)
            for code in fault_codes:
                code_upper = (code or "").upper()
                # Solo procesar si está listado y habilitado
                if not code_upper or not whitelist.get(code_upper, False):
                    continue

                # Asegurar existencia del código en catálogo (no crea relación maquinaria)
                OBD_Faults.objects.get_or_create(
                    code=code_upper,
                    defaults={'description': f'Falla OBD {code_upper}'}
                )

        except Exception as e:
            logger.error(f"Error procesando fallas OBD: {str(e)}")
    
    def get_parameter_by_avl_id(self, avl_id: int) -> Optional[Parameters]:
        """
        Obtiene un parámetro por su AVL ID
        
        Args:
            avl_id: ID del parámetro AVL
            
        Returns:
            Instancia de Parameters o None si no existe
        """
        try:
            return Parameters.objects.get(avl_id_parameter=avl_id)
        except Parameters.DoesNotExist:
            return None
    
    def filter_packet_by_device_parameters(self, packet: Dict, device_parameters: Optional[List[Parameters]]) -> Dict:
        """
        Filtra el paquete eliminando parámetros no configurados para el dispositivo.
        Solo se aplica al paquete procesado que se enviará por WebSocket.
        
        Args:
            packet: Paquete completo de telemetría (con alertas ya agregadas)
            device_parameters: Lista de parámetros permitidos para el dispositivo
            
        Returns:
            Paquete filtrado con solo parámetros configurados
        """
        if not device_parameters:
            # Si no hay parámetros configurados, devolver todo (compatibilidad hacia atrás)
            return packet
        
        # Crear conjunto de AVL IDs permitidos
        allowed_avl_ids = {p.avl_id_parameter for p in device_parameters if p.avl_id_parameter}
        
        # Mapeo de campo a AVL ID
        field_to_avl = {
            'ignition_status': 239,
            'movement_status': 240,
            'speed': 24,
            'gsm_signal': 21,
            'rpm': 36,
            'engine_temp': 32,
            'engine_load': 31,
            'oil_level': 1159,
            'fuel_level': 48,
            'fuel_used_gps': 12,
            'instant_consumption': 60,
            'odometer_total': 16,
            'odometer_trip': 199,
            'event_type': 253,
            'event_g_value': 254,
            'gps_location': 387,
            'obd_faults': 281,
        }
        
        # Crear copia del paquete para no modificar el original
        filtered_packet = packet.copy()
        
        # Filtrar datos dentro del paquete
        if 'data' in filtered_packet and isinstance(filtered_packet['data'], dict):
            filtered_data = filtered_packet['data'].copy()
            
            # Filtrar parámetros no configurados
            for field_name, avl_id in field_to_avl.items():
                if avl_id not in allowed_avl_ids:
                    # Eliminar parámetro no configurado
                    if field_name in filtered_data:
                        del filtered_data[field_name]
                        logger.debug(
                            f"Parámetro {field_name} (AVL_ID {avl_id}) filtrado del WebSocket "
                            f"(no configurado para el dispositivo)"
                        )
            
            filtered_packet['data'] = filtered_data
        
        return filtered_packet
    
    def store_telemetry_data(
        self,
        machinery: Machinery,
        device: TelemetryDevices,
        active_request: ServiceRequest,
        telemetry_data: Dict,
        timestamp: datetime,
        parameter_alerts: Dict[str, Tuple[bool, Optional[str]]],
        allowed_parameters: Optional[List[Parameters]] = None,
        user=None,
        logistic_status: Optional[str] = None
    ) -> int:
        """
        Almacena los datos de telemetría en la tabla 'data'
        Crea un registro por cada parámetro que tenga valor y esté configurado para el dispositivo
        
        Args:
            machinery: Instancia de Machinery
            device: Instancia de TelemetryDevices
            active_request: Solicitud activa asociada (OBLIGATORIO)
            telemetry_data: Diccionario con los datos de telemetría
            timestamp: Timestamp de la telemetría
            parameter_alerts: Diccionario {param_name: (is_alert, reason)}
            allowed_parameters: Lista de parámetros permitidos para este dispositivo (opcional)
            user: Instancia de User obtenida de RequestMachineryUser (OBLIGATORIO)
            logistic_status: Estado logístico calculado ("Ida", "Vuelta", "Trabajo" o None)
            
        Returns:
            Número de registros creados
        """
        records_created = 0
        
        # Validar que user no sea None
        if not user:
            logger.error("User es None. No se pueden crear registros sin usuario.")
            raise ValueError("User es requerido para almacenar datos de telemetría")
        
        try:
            # Crear conjunto de AVL IDs permitidos para validación rápida
            allowed_avl_ids = set()
            if allowed_parameters:
                allowed_avl_ids = {p.avl_id_parameter for p in allowed_parameters if p.avl_id_parameter}
            
            # Parámetros numéricos que se almacenan en 'data'
            numeric_fields = {
                'ignition_status': 239,
                'movement_status': 240,
                'speed': 24,
                'gsm_signal': 21,
                'rpm': 36,
                'engine_temp': 32,
                'engine_load': 31,
                'oil_level': 1159,
                'fuel_level': 48,
                'fuel_used_gps': 12,
                'instant_consumption': 60,
                'odometer_total': 16,
                'odometer_trip': 199,
                'event_type': 253,
                'event_g_value': 254,
            }
            
            # Guardar parámetros numéricos
            for field_name, avl_id in numeric_fields.items():
                value = telemetry_data.get(field_name)
                if value is not None:
                    try:
                        # VALIDACIÓN: Verificar si el parámetro está configurado para este dispositivo
                        if allowed_parameters and avl_id not in allowed_avl_ids:
                            logger.debug(
                                f"Parámetro {field_name} (AVL_ID {avl_id}) no está configurado "
                                f"para el dispositivo {device.name} (IMEI {device.IMEI}). Omitido."
                            )
                            continue
                        
                        parameter = self.get_parameter_by_avl_id(avl_id)
                        if not parameter:
                            logger.warning(f"Parámetro con AVL_ID {avl_id} ({field_name}) no encontrado en la base de datos")
                            continue
                        
                        # Verificar si tiene alerta para este parámetro
                        # Para event_type: alerta automática si tiene valor (incluye info de event_g_value)
                        # Para event_g_value: NO genera alerta separada, es parte del evento
                        if field_name == 'event_type':
                            is_alert = True  # Siempre alerta si hay evento registrado
                        elif field_name == 'event_g_value':
                            is_alert = False  # NO genera alerta separada, solo es parte del evento
                        else:
                            is_alert, _ = parameter_alerts.get(field_name, (False, None))
                        
                        Data.objects.create(
                            data=float(value),
                            id_parameter=parameter,
                            registered_at=timestamp,
                            id_device=device,
                            id_request=active_request,
                            id_machinery=machinery,
                            id_user=user,
                            alert=is_alert,
                            obd_fault=None
                        )
                        records_created += 1
                        
                    except Exception as e:
                        logger.error(f"Error guardando parámetro {field_name} (AVL_ID {avl_id}): {str(e)}")
                        continue
            
            # Manejar GPS: guardar latitud y longitud como dos registros consecutivos
            # Ambos usan el mismo AVL_ID (387) y el mismo timestamp
            gps_location = telemetry_data.get('gps_location')
            if gps_location:
                try:
                    # VALIDACIÓN: Verificar si GPS está configurado para este dispositivo
                    gps_avl_id = 387  # GPS location (AVL_ID 387) - usado para latitud y longitud
                    if allowed_parameters and gps_avl_id not in allowed_avl_ids:
                        logger.debug(
                            f"Parámetro GPS (AVL_ID {gps_avl_id}) no está configurado "
                            f"para el dispositivo {device.name} (IMEI {device.IMEI}). Omitido."
                        )
                    else:
                        match = re.match(r'\+([+-]?\d+\.?\d*)([+-]?\d+\.?\d*)/', gps_location)
                        if match:
                            lat_value = float(match.group(1))  # Latitud
                            lon_value = float(match.group(2))  # Longitud
                            
                            parameter = self.get_parameter_by_avl_id(gps_avl_id)
                            if parameter:
                                # 1. Guardar LATITUD primero (id_data menor, secuencial)
                                Data.objects.create(
                                    data=lat_value,
                                    id_parameter=parameter,
                                    registered_at=timestamp,
                                    id_device=device,
                                    id_request=active_request,
                                    id_machinery=machinery,
                                    id_user=user,
                                    alert=False,
                                    obd_fault=None
                                )
                                records_created += 1
                                
                                # 2. Guardar LONGITUD inmediatamente después (id_data mayor, consecutivo)
                                Data.objects.create(
                                    data=lon_value,
                                    id_parameter=parameter,  # Mismo parámetro (AVL_ID 387)
                                    registered_at=timestamp,  # Mismo timestamp exacto
                                    id_device=device,
                                    id_request=active_request,
                                    id_machinery=machinery,
                                    id_user=user,
                                    alert=False,
                                    obd_fault=None
                                )
                                records_created += 1
                                
                                logger.debug(f"GPS guardado: Lat={lat_value}, Lon={lon_value} (mismo timestamp)")
                except Exception as e:
                    logger.warning(f"Error procesando GPS: {str(e)}")
            
            # Procesar fallas OBD: se guardan en 'data' con obd_fault
            # Buscar parámetro OBD (AVL_ID 281 según documentación)
            obd_faults = telemetry_data.get('obd_faults', [])
            if obd_faults:
                obd_avl_id = 281  # OBD Faults
                # VALIDACIÓN: Verificar si OBD está configurado para este dispositivo
                if allowed_parameters and obd_avl_id not in allowed_avl_ids:
                    logger.debug(
                        f"Parámetro OBD (AVL_ID {obd_avl_id}) no está configurado "
                        f"para el dispositivo {device.name} (IMEI {device.IMEI}). Fallas OBD omitidas."
                    )
                else:
                    # Aplicar whitelist por maquinaria antes de guardar
                    whitelist = self._get_obd_whitelist(machinery)
                    obd_parameter = self.get_parameter_by_avl_id(obd_avl_id)
                    for fault_code in obd_faults:
                        try:
                            code_upper = (fault_code or "").upper()
                            if not code_upper or not whitelist.get(code_upper, False):
                                continue
                            if obd_parameter:
                                Data.objects.create(
                                    data=None,
                                    id_parameter=obd_parameter,
                                    registered_at=timestamp,
                                    id_device=device,
                                    id_request=active_request,
                                    id_machinery=machinery,
                                    id_user=user,
                                    alert=True,
                                    obd_fault=code_upper
                                )
                                records_created += 1
                            else:
                                logger.warning(f"Parámetro OBD (AVL_ID {obd_avl_id}) no encontrado. Falla {code_upper} no guardada en 'data'")
                        except Exception as e:
                            logger.error(f"Error guardando falla OBD {fault_code} en 'data': {str(e)}")
            
            # Guardar estado logístico (AVL_ID -1)
            if logistic_status:
                try:
                    logistic_avl_id = -1
                    logistic_parameter = self.get_parameter_by_avl_id(logistic_avl_id)
                    
                    if logistic_parameter:
                        # Convertir estado logístico a valor numérico
                        # 1 = Ida, 2 = Vuelta, 3 = Trabajo
                        status_map = {
                            "Ida": 1.0,
                            "Vuelta": 2.0,
                            "Trabajo": 3.0
                        }
                        status_value = status_map.get(logistic_status)
                        
                        if status_value is not None:
                            Data.objects.create(
                                data=status_value,
                                id_parameter=logistic_parameter,
                                registered_at=timestamp,
                                id_device=device,
                                id_request=active_request,
                                id_machinery=machinery,
                                id_user=user,
                                alert=False,
                                obd_fault=None
                            )
                            records_created += 1
                            logger.debug(f"Estado logístico guardado: {logistic_status} (valor: {status_value})")
                        else:
                            logger.warning(f"Estado logístico desconocido: {logistic_status}")
                    else:
                        logger.warning(f"Parámetro de estado logístico (AVL_ID -1) no encontrado en la base de datos")
                except Exception as e:
                    logger.error(f"Error guardando estado logístico: {str(e)}")
            
            logger.debug(f"Almacenados {records_created} registros en tabla 'data'")
            return records_created
            
        except Exception as e:
            logger.error(f"Error almacenando datos en tabla 'data': {str(e)}")
            raise
    
    @transaction.atomic
    def process_telemetry_packet(self, packet: Dict) -> bool:
        """
        Procesa un paquete completo de telemetría siguiendo el flujo especificado
        
        Args:
            packet: Diccionario con imei, timestamp y data
            
        Returns:
            True si se procesó correctamente, False en caso contrario
        """
        try:
            imei = packet.get('imei')
            timestamp_str = packet.get('timestamp')
            data = packet.get('data', {})
            
            if not imei or not timestamp_str or not data:
                logger.warning("Paquete incompleto recibido")
                return False
            
            # Parsear timestamp
            timestamp = datetime.fromisoformat(
                timestamp_str.replace('Z', '+00:00')
            ).astimezone(timezone.utc)
            
            # 1. Obtener dispositivo y maquinaria
            device_machinery = self.get_device_machinery(imei)
            if not device_machinery:
                logger.warning(f"No se encontro maquinaria para IMEI {imei}")
                return False
            
            device, machinery = device_machinery
            
            # 2. Consultar solicitudes activas
            active_requests = self.get_active_requests(timestamp.date())
            
            # 3. Buscar solicitud activa para esta maquinaria
            # VALIDACIÓN CRÍTICA: Si no hay solicitud activa, no se procesan ni guardan datos
            active_request = None
            request_machinery_user = None  # Guardar el objeto completo para obtener el usuario
            for req_id, req in active_requests.items():
                try:
                    request_machinery_user = RequestMachineryUser.objects.get(
                        request_id=req_id,
                        machinery=machinery
                    )
                    active_request = req
                    break
                except RequestMachineryUser.DoesNotExist:
                    continue
            
            # Si no hay solicitud activa para esta maquinaria en este día, no se guardan datos
            if not active_request or not request_machinery_user:
                logger.warning(
                    f"No se encontro solicitud activa para maquinaria {machinery.id_machinery} "
                    f"(IMEI {imei}) en fecha {timestamp.date()}. Datos descartados."
                )
                return False
            
            # 4. Obtener parámetros configurados (para validación posterior)
            device_parameters = self.get_device_parameters(device)
            
            # 5. Calcular estado logístico
            gps_location = data.get('gps_location', '')
            logistic_status = None
            if gps_location:
                logistic_status = self.calculate_logistic_status(
                    gps_location,
                    machinery,
                    active_requests
                )
            
            # 6. Validar umbrales y alertas para cada parámetro
            parameter_alerts = {}  # {param_name: (is_alert, reason)}
            
            # Crear conjunto de nombres de parámetros permitidos para validación rápida
            allowed_parameter_names = set()
            if device_parameters:
                allowed_parameter_names = {p.parameter_name for p in device_parameters if p.parameter_name}
            
            # Verificar umbrales para parámetros numéricos
            threshold_checks = [
                ('speed', data.get('speed')),
                ('engine_temp', data.get('engine_temp')),
                ('rpm', data.get('rpm')),
                ('oil_level', data.get('oil_level')),
                ('fuel_level', data.get('fuel_level')),
            ]
            
            total_alerts = 0
            for param_name, value in threshold_checks:
                if value is not None:
                    # VALIDACIÓN: Solo verificar umbrales si el parámetro está configurado para el dispositivo
                    if device_parameters and param_name not in allowed_parameter_names:
                        logger.debug(
                            f"Parámetro {param_name} no está configurado para el dispositivo "
                            f"{device.name} (IMEI {device.IMEI}). Umbrales omitidos."
                        )
                        continue
                    
                    is_alert, reason = self.check_thresholds(machinery, param_name, float(value))
                    parameter_alerts[param_name] = (is_alert, reason)
                    if is_alert:
                        total_alerts += 1
            
            # Alertas de eventos controladas por event_type_machinery
            event_type_avl_id = 253
            event_g_value_avl_id = 254

            event_cfg = self._get_event_type_config(machinery)
            event_type = data.get('event_type')
            event_g_value = data.get('event_g_value')

            # Respetar configuración por dispositivo (si existe)
            device_allows_event = True
            if device_parameters:
                device_allows_event = any(p.avl_id_parameter == event_type_avl_id for p in device_parameters)

            if device_allows_event and self._event_permitted(event_type, event_g_value, event_cfg):
                if event_g_value is not None:
                    alert_reason = f"Evento detectado (Tipo: {event_type}, Valor G: {event_g_value})"
                else:
                    alert_reason = f"Evento detectado (Tipo: {event_type})"
                parameter_alerts['event_type'] = (True, alert_reason)
                total_alerts += 1
            
            # 7. Procesar fallas OBD
            obd_faults = data.get('obd_faults', [])
            if obd_faults:
                self.process_obd_faults(machinery, obd_faults, timestamp)
            
            # 8. Almacenar datos en tabla 'data' (un registro por parámetro)
            # Pasar los parámetros permitidos para validación
            records_created = self.store_telemetry_data(
                machinery=machinery,
                device=device,
                active_request=active_request,
                telemetry_data=data,
                timestamp=timestamp,
                parameter_alerts=parameter_alerts,
                allowed_parameters=device_parameters,
                user=request_machinery_user.user,  # Pasar el usuario desde RequestMachineryUser
                logistic_status=logistic_status  # Pasar el estado logístico calculado
            )
            
            # 9. Agregar alertas al paquete original para incluir en WebSocket
            # Construir lista de alertas con formato para el WebSocket
            alerts_list = []
            for param_name, (is_alert, reason) in parameter_alerts.items():
                if is_alert and reason:
                    alerts_list.append({
                        'parameter': param_name,
                        'reason': reason
                    })
            
            # Agregar alertas al paquete
            packet['alerts'] = alerts_list if alerts_list else None
            
            # Agregar request_id al paquete (necesario para filtrar por solicitud en WebSocket/SSE)
            packet['request_id'] = active_request.id_request
            
            # Agregar información de maquinaria y operario al paquete
            packet['serial_number'] = machinery.serial_number
            packet['machinery_name'] = machinery.machinery_name
            
            # Obtener nombre del operario desde el servicio externo
            operator_name = None
            if request_machinery_user and request_machinery_user.user:
                operator_name = self._get_operator_name(request_machinery_user.user.id_user)
            packet['operator_name'] = operator_name
            
            # Filtrar parámetros no configurados antes de enviar por WebSocket
            filtered_packet = self.filter_packet_by_device_parameters(packet, device_parameters)
            
            logger.info(
                f"Paquete procesado: Request ID {active_request.id_request}, "
                f"IMEI {imei}, "
                f"Serial: {machinery.serial_number}, "
                f"Maquinaria: {machinery.machinery_name}, "
                f"Operario: {operator_name or 'N/A'}, "
                f"Estado logístico: {logistic_status}, "
                f"Registros creados: {records_created}, "
                f"Alertas: {total_alerts}"
            )
            
            return filtered_packet  # Retornar paquete filtrado con alertas agregadas
            
        except Exception as e:
            logger.error(f"Error procesando paquete: {str(e)}", exc_info=True)
            return False
    
    async def connect_and_process(self):
        """
        Conecta al WebSocket y procesa mensajes continuamente
        """
        logger.info(f"Conectando a {self.simulator_url}...")
        
        while self.is_running:
            try:
                async with websockets.connect(self.simulator_url) as websocket:
                    logger.info("Conectado al simulador de telemetria")
                    
                    async for message in websocket:
                        if not self.is_running:
                            break
                            
                        try:
                            packet = json.loads(message)
                            
                            # Ignorar paquetes que ya tienen alertas (ya fueron procesados)
                            # Estos son paquetes que el procesador mismo envió de vuelta al simulador
                            if packet.get('alerts') is not None:
                                logger.debug(f"Paquete ya procesado ignorado (tiene alertas) - IMEI: {packet.get('imei', 'N/A')}")
                                continue
                            
                            # Crear identificador único del paquete: IMEI + timestamp
                            imei = packet.get('imei', 'UNKNOWN')
                            timestamp = packet.get('timestamp', '')
                            packet_id = f"{imei}_{timestamp}"
                            
                            # Limpiar cache antiguo (más de 5 minutos)
                            now = datetime.now(timezone.utc)
                            self._processed_packets_cache = {
                                pid: ptime for pid, ptime in self._processed_packets_cache.items()
                                if (now - ptime).total_seconds() < 300
                            }
                            
                            # Verificar si ya se procesó este paquete
                            if packet_id in self._processed_packets_cache:
                                logger.debug(f"Paquete duplicado ignorado - IMEI: {imei}, TS: {timestamp}")
                                continue
                            
                            logger.debug(f"Paquete recibido - IMEI: {imei}, TS: {timestamp}")
                            
                            # Procesar en hilo separado para no bloquear
                            # Usar sync_to_async para llamadas a Django ORM
                            from asgiref.sync import sync_to_async
                            
                            result = await sync_to_async(self.process_telemetry_packet)(packet)
                            
                            # Marcar paquete como procesado en el cache
                            self._processed_packets_cache[packet_id] = datetime.now(timezone.utc)
                            
                            # Si el procesamiento fue exitoso y retornó un paquete con alertas, reenviarlo
                            if result and isinstance(result, dict) and 'alerts' in result:
                                # El paquete ahora incluye alertas, enviarlo al simulador para reenvío
                                await self._send_processed_packet_to_simulator(result)
                            elif not result:
                                logger.debug("Paquete procesado pero no guardado (probablemente sin solicitud activa)")
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Error decodificando JSON: {str(e)}")
                        except Exception as e:
                            logger.error(f"Error procesando mensaje: {str(e)}", exc_info=True)
                            
            except websockets.exceptions.ConnectionClosed:
                if self.is_running:
                    logger.warning("Conexion cerrada, reintentando en 5 segundos...")
                    await asyncio.sleep(5)
            except Exception as e:
                if self.is_running:
                    logger.error(f"Error de conexion: {str(e)}", exc_info=True)
                    logger.info("Reintentando conexion en 10 segundos...")
                    await asyncio.sleep(10)
    
    def start(self):
        """
        Inicia el procesador
        """
        # Validar tablas
        self.validate_tables_exist()
        
        self.is_running = True
        logger.info("Procesador de telemetria iniciado")
        
        # Ejecutar loop asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect_and_process())
        except Exception as e:
            logger.error(f"Error en el loop de asyncio: {str(e)}", exc_info=True)
            raise
        finally:
            loop.close()
    
    async def _send_processed_packet_to_simulator(self, packet: Dict[str, Any]):
        """
        Envía el paquete procesado con alertas al simulador para que lo reenvíe por WebSocket
        
        Args:
            packet: Paquete de telemetría con alertas agregadas
        """
        try:
            # Enviar paquete procesado al endpoint HTTP del simulador
            async with aiohttp.ClientSession() as session:
                endpoint_url = f"{self.simulator_http_url}/api/broadcast-processed"
                async with session.post(endpoint_url, json=packet, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('success'):
                            alerts_count = len(packet.get('alerts', [])) if packet.get('alerts') else 0
                            logger.debug(f"Paquete con {alerts_count} alertas reenviado exitosamente")
                        else:
                            logger.warning(f"Error reenviando paquete: {result.get('message', 'Unknown error')}")
                    else:
                        logger.warning(f"Error HTTP {response.status} al reenviar paquete procesado")
        except aiohttp.ClientError as e:
            logger.warning(f"Error de conexión al reenviar paquete: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado reenviando paquete: {str(e)}")
    
    def stop(self):
        """
        Detiene el procesador
        """
        self.is_running = False
        logger.info("Procesador de telemetria detenido")


def run_processor():
    """
    Función para ejecutar el procesador como script independiente
    """
    import django
    import os
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
    django.setup()
    
    processor = TelemetryProcessor()
    try:
        processor.start()
    except KeyboardInterrupt:
        logger.info("Deteniendo procesador...")
        processor.stop()


if __name__ == "__main__":
    run_processor()

