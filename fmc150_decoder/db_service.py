"""
Servicio para consultar nombres de parámetros desde la base de datos
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'machpaydb'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

@lru_cache(maxsize=1)
def get_parameter_names_from_db():
    """
    Obtiene el mapeo de AVL IDs a nombres desde la base de datos.
    Usa cache para evitar consultas repetidas.
    
    Returns:
        dict: Diccionario {avl_id: parameter_name}
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT avl_id_parameter, parameter_name 
            FROM parameters 
            WHERE avl_id_parameter IS NOT NULL
        """)
        
        results = cursor.fetchall()
        io_names = {row['avl_id_parameter']: row['parameter_name'] for row in results}
        
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Cargados {len(io_names)} parámetros desde BD")
        return io_names
    except Exception as e:
        logger.error(f"⚠️ Error consultando base de datos: {e}")
        logger.warning("📋 Usando diccionario por defecto...")
        # Fallback básico
        return {
            12: "Fuel Used GPS",
            16: "Total Odometer",
            21: "GSM Signal",
            24: "Speed",
            31: "Engine Load",
            32: "Engine Temp",
            36: "RPM",
            48: "Fuel Level",
            60: "Instant Consumption",
            199: "Trip Odometer",
            239: "Ignition",
            240: "Movement",
            253: "Event Type",
            254: "Event G Value",
            281: "OBD Faults",
            387: "GPS Location",
            1159: "Oil Level",
        }

def get_parameter_name(io_id):
    """
    Obtiene el nombre del parámetro desde la BD
    
    Args:
        io_id: ID del parámetro AVL
    
    Returns:
        str: Nombre del parámetro o el ID como string si no se encuentra
    """
    io_names = get_parameter_names_from_db()
    return io_names.get(io_id, str(io_id))

def clear_cache():
    """Limpia el cache para forzar recarga desde BD"""
    get_parameter_names_from_db.cache_clear()
    logger.info("🔄 Cache de parámetros limpiado")

