"""
Pydantic models for telemetry data structures
"""
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class TelemetryData(BaseModel):
    """Data payload for telemetry measurements"""
    
    # ID 239: Estado de Ignición (0 = OFF, 1 = ON)
    ignition_status: int = Field(..., ge=0, le=1, description="Estado de ignición")
    
    # ID 240: Estado de Movimiento (0 = Detenido, 1 = Moviéndose)
    movement_status: int = Field(..., ge=0, le=1, description="Estado de movimiento")
    
    # ID 24: Velocidad Actual (km/h)
    speed: int = Field(..., ge=0, le=350, description="Velocidad en km/h")
    
    # ID 387: Ubicación GPS en formato ISO6709
    gps_location: str = Field(..., description="Ubicación GPS formato ISO6709")
    
    # ID 21: Señal GSM (1=Excelente, 5=Pérdida)
    gsm_signal: int = Field(..., ge=1, le=5, description="Nivel de señal GSM")
    
    # ID 36: Revoluciones del motor (RPM)
    rpm: int = Field(..., ge=0, le=16384, description="Revoluciones por minuto")
    
    # ID 32: Temperatura del Motor (°C)
    engine_temp: int = Field(..., ge=-60, le=127, description="Temperatura del motor en °C")
    
    # ID 31: Carga del Motor (%)
    engine_load: int = Field(..., ge=0, le=100, description="Carga del motor en %")
    
    # ID 1159: Nivel de Aceite (%)
    oil_level: int = Field(..., ge=0, le=100, description="Nivel de aceite en %")
    
    # ID 48: Nivel de Combustible (%)
    fuel_level: int = Field(..., ge=0, le=100, description="Nivel de combustible en %")
    
    # ID 12: Combustible Usado GPS (litros)
    fuel_used_gps: float = Field(..., ge=0, le=4294967, description="Combustible usado según GPS en litros")
    
    # ID 60: Consumo instantáneo (L/h)
    instant_consumption: float = Field(..., ge=0, le=32767, description="Consumo instantáneo en L/h")
    
    # ID 281: Fallas OBD
    obd_faults: List[str] = Field(default_factory=list, description="Lista de códigos de fallas OBD")
    
    # ID 16: Odómetro Total (metros)
    odometer_total: int = Field(..., ge=0, le=2147483647, description="Odómetro total en metros")
    
    # ID 199: Odómetro del Viaje (metros)
    odometer_trip: int = Field(..., ge=0, le=2147483647, description="Odómetro del viaje en metros")
    
    # ID 253: Tipo de Evento (1=Aceleración, 2=Frenado, 3=Curva)
    event_type: Optional[int] = Field(None, ge=1, le=3, description="Tipo de evento")
    
    # ID 254: Valor G del Evento
    event_g_value: Optional[int] = Field(None, ge=0, le=255, description="Valor G del evento")


class TelemetryPacket(BaseModel):
    """Complete telemetry packet with IMEI, timestamp, and data"""
    
    imei: str = Field(
        ..., 
        min_length=15, 
        max_length=15, 
        pattern=r'^\d{15}$',
        description="IMEI del dispositivo (15 dígitos)"
    )
    timestamp: str = Field(..., description="Timestamp en formato ISO 8601 UTC")
    data: TelemetryData = Field(..., description="Datos de telemetría")
    alerts: Optional[List[Dict[str, str]]] = Field(
        default=None, 
        description="Lista de alertas detectadas por el procesador. Formato: [{'parameter': 'speed', 'reason': 'Valor por encima del máximo'}]"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "imei": "352099001761481",
                "timestamp": "2025-10-27T13:30:00.123456Z",
                "data": {
                    "ignition_status": 1,
                    "movement_status": 1,
                    "speed": 120,
                    "gps_location": "+04.60971-074.08175/",
                    "gsm_signal": 4,
                    "rpm": 2500,
                    "engine_temp": 92,
                    "engine_load": 57,
                    "oil_level": 80,
                    "fuel_level": 68,
                    "fuel_used_gps": 153.2,
                    "instant_consumption": 14.5,
                    "obd_faults": ["P0135", "P0420"],
                    "odometer_total": 2456789,
                    "odometer_trip": 34567,
                    "event_type": 2,
                    "event_g_value": 45
                }
            }
        }
    }

