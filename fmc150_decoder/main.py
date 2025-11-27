"""
Main FastAPI application for FMC150 Decoder Service
"""
import logging
import threading
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager

# Import websocket manager and the TCP server
from fmc150_decoder.websocket import manager
from fmc150_decoder.server import FMC150Server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable for the TCP server thread
tcp_server_thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle events
    """
    global tcp_server_thread
    # Startup
    logger.info("FMC150 Decoder Service iniciándose...")
    
    # Create an instance of the TCP server and pass the websocket manager
    fmc150_server = FMC150Server(manager)
    
    # Run the TCP server in a background thread
    tcp_server_thread = threading.Thread(target=fmc150_server.run, daemon=True)
    tcp_server_thread.start()
    logger.info("Servidor TCP para dispositivos FMC150 iniciado en segundo plano.")
    
    logger.info("Servicio WebSocket para datos reales disponible en: ws://localhost:8004/ws/telemetria_real")
    yield
    # Shutdown
    logger.info("Deteniendo FMC150 Decoder Service...")
    # The TCP server thread is a daemon, so it will exit when the main app exits.

# Create FastAPI application
app = FastAPI(
    title="FMC150 Decoder Service",
    description="Recibe, decodifica y transmite datos de telemetría real de dispositivos FMC150.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": "FMC150 Decoder",
        "version": "1.0.0",
        "status": "running",
        "description": "Este servicio escucha datos de dispositivos GPS, los decodifica y los transmite vía WebSocket.",
        "websocket_endpoint": "/ws/telemetria_real"
    }

@app.websocket("/ws/telemetria_real")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real telemetry data streaming.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive, waiting for messages or disconnection
            data = await websocket.receive_text()
            logger.debug(f"Mensaje recibido en websocket de datos reales: {data}")
    except Exception:
        manager.disconnect(websocket)
