"""
WebSocket endpoint for real-time telemetry data streaming
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from app.simulator.generator import TelemetryGenerator

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts telemetry data"""
    
    def __init__(self):
        """Initialize with empty connections list"""
        self.active_connections: List[WebSocket] = []
        self.generator = TelemetryGenerator()
        self.is_running = False
        self.broadcast_task = None
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nueva conexión WebSocket establecida. Total: {len(self.active_connections)}")
        
        # Start broadcasting if not already running
        if not self.is_running:
            await self._start_broadcasting()
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Conexión WebSocket cerrada. Total: {len(self.active_connections)}")
        
        # Stop broadcasting if no connections
        if len(self.active_connections) == 0 and self.is_running:
            self._stop_broadcasting()
    
    async def _start_broadcasting(self):
        """Start broadcasting telemetry data every 30 seconds"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Iniciando transmisión de datos de telemetría cada 30 segundos...")
        
        try:
            while self.is_running and len(self.active_connections) > 0:
                # Generate new telemetry data
                telemetry_packet = self.generator.generate_response()
                
                # Log packet info
                imei = telemetry_packet.get("imei", "UNKNOWN")
                timestamp = telemetry_packet.get("timestamp", "UNKNOWN")
                logger.info(f"Enviando paquete - IMEI: {imei}, TS: {timestamp}")
                
                # Convert to JSON
                message = json.dumps(telemetry_packet, default=str)
                
                # Broadcast to all connected clients
                await self._broadcast(message)
                
                # Wait 30 seconds before next transmission
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"Error en broadcasting: {str(e)}")
        finally:
            self.is_running = False
            logger.info("Broadcasting detenido")
    
    def _stop_broadcasting(self):
        """Stop the broadcasting loop"""
        self.is_running = False
        logger.info("Solicitud de detener broadcasting")
    
    async def _broadcast(self, message: str):
        """Send message to all connected clients"""
        if not self.active_connections:
            return
        
        # Broadcast to all clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error enviando mensaje a cliente: {str(e)}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_processed_packet(self, packet: dict):
        """
        Reenvía un paquete procesado con alertas agregadas a todos los clientes conectados
        
        Args:
            packet: Diccionario con el paquete de telemetría procesado (incluye alertas)
        """
        try:
            message = json.dumps(packet, default=str)
            await self._broadcast(message)
            if packet.get('alerts'):
                logger.debug(f"Reenviando paquete con {len(packet.get('alerts', []))} alertas")
        except Exception as e:
            logger.error(f"Error reenviando paquete procesado: {str(e)}")


# Global connection manager instance
manager = ConnectionManager()


async def websocket_telemetry_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for telemetry data streaming
    
    Usage:
        Connect to: ws://localhost:8000/ws/telemetria
        Receive JSON data every 30 seconds
    """
    await manager.connect(websocket)
    
    try:
        # Keep connection alive and handle any incoming messages
        while True:
            # Wait for any message from client (keep-alive, ping, etc.)
            data = await websocket.receive_text()
            
            # Log received message (if any)
            if data:
                logger.debug(f"Mensaje recibido del cliente: {data}")
            
            # You can add custom message handling here if needed
            # For now, just keep the connection alive
            
    except WebSocketDisconnect:
        logger.info("Cliente desconectado del WebSocket")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")
        manager.disconnect(websocket)
        await websocket.close()

