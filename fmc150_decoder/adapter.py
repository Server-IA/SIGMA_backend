"""
Adaptador que convierte datos decodificados del FMC150 al formato TelemetryPacket
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)

def convert_fmc150_to_telemetry_packet(decoded_reg, imei):
    """
    Convierte un registro decodificado del FMC150 al formato TelemetryPacket
    
    Args:
        decoded_reg: Registro decodificado del FMC150 (dict con 'io', 'gps', 'timestamp')
        imei: IMEI del dispositivo
    
    Returns:
        dict: TelemetryPacket compatible con el generador
    """
    io = decoded_reg.get('io', {})
    gps = decoded_reg.get('gps', {})
    
    # Mapeo de nombres de parámetros a campos del TelemetryPacket
    # Usa los nombres que vienen de la BD
    def get_io_value(name_or_id, default=None):
        # Buscar por nombre primero
        if name_or_id in io:
            return io[name_or_id]
        # Si no, buscar por ID
        if isinstance(name_or_id, int) and str(name_or_id) in io:
            return io[str(name_or_id)]
        return default
    
    # Convertir GPS a formato ISO6709
    lat = gps.get('latitude', 0)
    lon = gps.get('longitude', 0)
    gps_location = f"+{lat:.5f}{lon:.5f}/" if lat and lon else "+00.00000-000.00000/"
    
    # Procesar OBD faults si existen
    obd_faults = []
    obd_value = get_io_value("OBD Faults")
    if obd_value:
        # Si es un string hexadecimal, podría contener códigos OBD
        # Por ahora, dejamos vacío y se procesará después
        pass
    
    # Construir paquete en formato TelemetryPacket
    packet = {
        "imei": imei,
        "timestamp": decoded_reg.get('timestamp', datetime.now(ZoneInfo("America/Bogota")).isoformat()),
        "data": {
            "ignition_status": get_io_value("Ignition", 0),
            "movement_status": get_io_value("Movement", 0),
            "speed": get_io_value("Speed", 0),
            "gps_location": gps_location,
            "gsm_signal": get_io_value("GSM Signal", 1),
            "rpm": get_io_value("RPM", 0),
            "engine_temp": get_io_value("Engine Temp", 0),
            "engine_load": get_io_value("Engine Load", 0),
            "oil_level": get_io_value("Oil Level", 0),
            "fuel_level": get_io_value("Fuel Level", 0),
            "fuel_used_gps": float(get_io_value("Fuel Used GPS", 0.0)),
            "instant_consumption": float(get_io_value("Instant Consumption", 0.0)),
            "obd_faults": obd_faults,
            "odometer_total": get_io_value("Total Odometer", 0),
            "odometer_trip": get_io_value("Trip Odometer", 0),
            "event_type": get_io_value("Event Type"),
            "event_g_value": get_io_value("Event G Value"),
        },
        "alerts": None  # Se agregará después del procesamiento
    }
    
    return packet

