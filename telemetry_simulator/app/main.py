"""
Main FastAPI application for Telemetry Simulator
"""
import logging
from fastapi import FastAPI, WebSocket, Query
from fastapi.responses import StreamingResponse
import asyncio
import json
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
async def websocket_endpoint_processor(
    websocket: WebSocket, 
    processor: bool = Query(True),  # Por defecto True, solo para procesadores
    password: str = Query(None, description="Contraseña requerida para conectarse al WebSocket")
):
    """
    WebSocket endpoint SOLO para procesadores (sin request_id)
    
    Args:
        processor: Debe ser True (solo procesadores pueden usar esta ruta)
        password: Contraseña requerida para conectarse al WebSocket
    
    Procesador:
        Connects to: ws://localhost:8003/ws/telemetria?processor=true&password=telemetry_password_2024
        Receives: Datos sin procesar para procesar y generar alertas
    """
    if not processor:
        await websocket.close(code=4003, reason="Esta ruta es solo para procesadores. Use /ws/telemetria/{request_id} para clientes")
        return
    
    # Validar contraseña antes de aceptar la conexión
    if password != settings.WEBSOCKET_PASSWORD:
        logger.warning(f"Intento de conexión con contraseña incorrecta")
        await websocket.close(code=4001, reason="Contraseña incorrecta")
        return
    
    # Contraseña válida, proceder con la conexión (sin request_id para procesadores)
    await websocket_telemetry_endpoint(websocket, is_processor=True, request_id=None)


@app.websocket("/ws/telemetria/{request_id}")
async def websocket_endpoint_client(
    websocket: WebSocket,
    request_id: str,
    password: str = Query(None, description="Contraseña requerida para conectarse al WebSocket")
):
    """
    WebSocket endpoint para clientes (con request_id obligatorio)
    
    Args:
        request_id: ID de la solicitud a monitorear (obligatorio)
        password: Contraseña requerida para conectarse al WebSocket
    
    Cliente normal:
        Connects to: ws://localhost:8003/ws/telemetria/{request_id}?password=telemetry_password_2024
        Receives: Solo datos procesados con alertas de la solicitud especificada (cada 5 segundos aprox)
    
    Returns:
        - JSON with timestamp and telemetry data including:
            - Ignition status, movement status, speed, GPS location
            - RPM, engine temperature, engine load
            - Oil level, fuel level, fuel consumption
            - OBD faults, odometer readings
            - Event types and G-values
            - alerts (solo en datos procesados)
            - request_id, serial_number, machinery_name, operator_name
    """
    # Validar contraseña antes de aceptar la conexión
    if password != settings.WEBSOCKET_PASSWORD:
        logger.warning(f"Intento de conexión con contraseña incorrecta")
        await websocket.close(code=4001, reason="Contraseña incorrecta")
        return
    
    # Contraseña válida, proceder con la conexión (con request_id para clientes)
    await websocket_telemetry_endpoint(websocket, is_processor=False, request_id=request_id)


@app.get("/api/telemetria/stream/{request_id}")
async def telemetry_stream(
    request_id: str,
    password: str = Query(None, description="Contraseña requerida para conectarse al stream")
):
    """
    Server-Sent Events (SSE) endpoint para streaming de telemetría procesada por solicitud.

    Args:
        request_id: ID de la solicitud a monitorear (obligatorio)
        password: Contraseña requerida para conectarse al stream

    Uso:
        GET /api/telemetria/stream/{request_id}?password=...
        
    Retorna:
        - Stream de datos procesados con alertas solo de la solicitud especificada
        - Cada evento incluye: imei, request_id, serial_number, machinery_name, operator_name, data, alerts
    """
    # Validar contraseña antes de iniciar el stream
    if password != settings.WEBSOCKET_PASSWORD:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={"error": "Contraseña incorrecta"}
        )

    # Enviar mensaje inicial de confirmación (sin validar existencia - el timeout manejará si no hay datos)
    confirmation_data = {
        "type": "connection_confirmed",
        "request_id": request_id,
        "message": f"Conexión establecida exitosamente para la solicitud '{request_id}'",
        "status": "waiting_for_data",
        "timeout_seconds": manager.data_timeout_seconds
    }
    
    # Crear cola por cliente y registrar consumidor SSE con request_id
    queue: asyncio.Queue = asyncio.Queue(maxsize=10)
    unsubscribe = manager.register_sse_consumer(queue, request_id)

    async def event_generator():
        try:
            # Enviar mensaje inicial de confirmación
            yield f"data: {json.dumps(confirmation_data, default=str)}\n\n"
            
            while True:
                packet = await queue.get()
                # Verificar que el paquete coincida con el request_id (doble verificación)
                if packet.get('request_id') == request_id:
                    yield f"data: {json.dumps(packet, default=str)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            # Asegurar desuscripción
            unsubscribe()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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

