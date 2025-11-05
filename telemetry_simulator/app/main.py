"""
Main FastAPI application for Telemetry Simulator
"""
import logging
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.websocket import websocket_telemetry_endpoint, manager
from app.config import settings
from app.models.telemetry_data import TelemetryPacket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle events
    """
    # Startup
    logger.info("Telemetry Simulator iniciándose...")
    
    # Validate IMEI configuration
    try:
        imeis = settings.imei_list
        logger.info(f"IMEI configurado: {len(imeis)} dispositivo(s)")
        
        # Try to get first IMEI to validate
        initial_imei = settings.validate_imei_config()
        logger.info(f"IMEI inicial: {initial_imei}")
    except Exception as e:
        logger.error(f"Error en configuración de IMEI: {str(e)}")
        raise
    
    logger.info("Servicio WebSocket disponible en: ws://localhost:8000/ws/telemetria")
    logger.info("Servicio listo para recibir conexiones")
    yield
    # Shutdown
    logger.info("Deteniendo Telemetry Simulator...")


# Create FastAPI application
app = FastAPI(
    title="Telemetry Simulator",
    description="Servicio de simulación de telemetría vehicular en tiempo real",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": "Telemetry Simulator",
        "version": "1.0.0",
        "description": "Servicio de simulación de telemetría vehicular",
        "websocket_endpoint": "/ws/telemetria",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with IMEI configuration status
    """
    imeis = settings.imei_list
    
    return {
        "status": "healthy",
        "service": "Telemetry Simulator",
        "imei_config": {
            "configured_imeis": len(imeis),
            "allow_generate_imei": settings.ALLOW_GENERATE_IMEI,
            "imeis_preview": imeis[:3] if imeis else []
        }
    }


@app.post("/api/broadcast-processed")
async def broadcast_processed_packet(packet: dict):
    """
    Endpoint para recibir un paquete procesado con alertas y reenviarlo por WebSocket
    
    Este endpoint es llamado por el procesador de telemetría después de validar
    los datos y calcular las alertas. El paquete incluye el campo 'alerts'.
    """
    try:
        await manager.broadcast_processed_packet(packet)
        return {
            "success": True,
            "message": "Paquete procesado reenviado exitosamente",
            "alerts_count": len(packet.get("alerts", [])) if packet.get("alerts") else 0
        }
    except Exception as e:
        logger.error(f"Error reenviando paquete procesado: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


@app.websocket("/ws/telemetria")
async def websocket_endpoint(
    websocket: WebSocket, 
    processor: bool = Query(False),
    password: str = Query(..., description="Contraseña requerida para conectarse al WebSocket")
):
    """
    WebSocket endpoint for telemetry data streaming
    
    Args:
        processor: Si es True, marca la conexión como procesador (recibe datos sin procesar)
                   Si es False, es un cliente normal (solo recibe datos procesados)
        password: Contraseña requerida para conectarse al WebSocket (variable de entorno WEBSOCKET_PASSWORD)
    
    Cliente normal:
        Connects to: ws://localhost:8003/ws/telemetria?password=telemetry_password_2024
        Receives: Solo datos procesados con alertas (cada 30 segundos aprox)
    
    Procesador:
        Connects to: ws://localhost:8003/ws/telemetria?processor=true&password=telemetry_password_2024
        Receives: Datos sin procesar para procesar y generar alertas
    
    Returns:
        - JSON with timestamp and telemetry data including:
            - Ignition status, movement status, speed, GPS location
            - RPM, engine temperature, engine load
            - Oil level, fuel level, fuel consumption
            - OBD faults, odometer readings
            - Event types and G-values
            - alerts (solo en datos procesados)
    """
    # Validar contraseña antes de aceptar la conexión
    if password != settings.WEBSOCKET_PASSWORD:
        logger.warning(f"Intento de conexión con contraseña incorrecta")
        await websocket.close(code=4001, reason="Contraseña incorrecta")
        return
    
    # Contraseña válida, proceder con la conexión
    await websocket_telemetry_endpoint(websocket, is_processor=processor)


@app.on_event("startup")
async def startup_event():
    """Additional startup tasks if needed"""
    logger.info("Iniciando servicios adicionales...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks on shutdown"""
    logger.info("Cerrando servicios...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

