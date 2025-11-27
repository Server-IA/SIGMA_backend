"""
WebSocket endpoint for real-time REAL telemetry data streaming from FMC150
"""
import asyncio
import json
import logging
from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts real telemetry data"""

    def __init__(self):
        """Initialize with empty connections list"""
        self.active_connections: List[WebSocket] = []
        logger.info("Connection Manager para datos reales inicializado.")

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nuevo cliente conectado al stream de datos reales. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Cliente desconectado del stream de datos reales. Total: {len(self.active_connections)}")

    async def broadcast_real_data(self, packet: dict):
        """Broadcasts a real data packet to all connected clients"""
        if not self.active_connections:
            return

        try:
            message = json.dumps(packet, default=str)
            imei = packet.get('imei', 'UNKNOWN')
            logger.info(f"Transmitiendo paquete real (IMEI: {imei}) a {len(self.active_connections)} cliente(s)")
            
            disconnected_clients = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected_clients.append(connection)
            
            for client in disconnected_clients:
                self.disconnect(client)

        except Exception as e:
            logger.error(f"Error transmitiendo paquete real: {str(e)}")


# Global connection manager instance
manager = ConnectionManager()
