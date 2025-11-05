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
        self.processor_connections: List[WebSocket] = []  # Conexiones del procesador
        self.generator = TelemetryGenerator()
        self.is_running = False
        self.broadcast_task = None
    
    async def connect(self, websocket: WebSocket, is_processor: bool = False):
        """Accept new WebSocket connection
        
        Args:
            websocket: Conexión WebSocket
            is_processor: Si es True, es una conexión del procesador (recibe datos sin procesar)
        """
        await websocket.accept()
        
        if is_processor:
            self.processor_connections.append(websocket)
            logger.info(f"Conexión del procesador establecida. Total procesadores: {len(self.processor_connections)}")
        else:
            self.active_connections.append(websocket)
            logger.info(f"Nueva conexión WebSocket establecida. Total clientes: {len(self.active_connections)}")
        
        # Start data generation for processor if not already running
        if not self.is_running:
            await self._start_data_generation()
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.processor_connections:
            self.processor_connections.remove(websocket)
            logger.info(f"Conexión del procesador cerrada. Total procesadores: {len(self.processor_connections)}")
        elif websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Conexión WebSocket cerrada. Total clientes: {len(self.active_connections)}")
        
        # Stop data generation if no processor connections
        if len(self.processor_connections) == 0 and self.is_running:
            self._stop_data_generation()
    
    async def _start_data_generation(self):
        """Start generating telemetry data every 30 seconds and send only to processor"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Iniciando generación de datos de telemetría cada 30 segundos (solo para procesador)...")
        
        try:
            while self.is_running and len(self.processor_connections) > 0:
                # Generate new telemetry data
                telemetry_packet = self.generator.generate_response()
                
                # Log packet info
                imei = telemetry_packet.get("imei", "UNKNOWN")
                timestamp = telemetry_packet.get("timestamp", "UNKNOWN")
                logger.info(f"Generando paquete para procesador - IMEI: {imei}, TS: {timestamp}")
                
                # Convert to JSON
                message = json.dumps(telemetry_packet, default=str)
                
                # Send ONLY to processor connections (not to regular clients)
                await self._send_to_processors(message)
                
                # Wait 30 seconds before next transmission
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"Error en generación de datos: {str(e)}")
        finally:
            self.is_running = False
            logger.info("Generación de datos detenida")
    
    def _stop_data_generation(self):
        """Stop the data generation loop"""
        self.is_running = False
        logger.info("Solicitud de detener generación de datos")
    
    async def _send_to_processors(self, message: str):
        """Send message only to processor connections"""
        if not self.processor_connections:
            return
        
        disconnected = []
        for connection in self.processor_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Error enviando mensaje al procesador: {str(e)}")
                disconnected.append(connection)
        
        # Remove disconnected processors
        for conn in disconnected:
            self.disconnect(conn)
    
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
        
        Este es el ÚNICO método que envía datos a los clientes normales.
        Solo se llama cuando el TelemetryProcessor ha procesado los datos.
        
        Args:
            packet: Diccionario con el paquete de telemetría procesado (incluye alertas)
        """
        try:
            message = json.dumps(packet, default=str)
            # Enviar solo a clientes normales (no a procesadores)
            await self._broadcast(message)
            
            alerts_count = len(packet.get('alerts', [])) if packet.get('alerts') else 0
            imei = packet.get('imei', 'UNKNOWN')
            logger.info(f"Enviando paquete procesado a {len(self.active_connections)} cliente(s) - IMEI: {imei}, Alertas: {alerts_count}")
        except Exception as e:
            logger.error(f"Error reenviando paquete procesado: {str(e)}")


# Global connection manager instance
manager = ConnectionManager()


async def websocket_telemetry_endpoint(websocket: WebSocket, is_processor: bool = False):
    """
    WebSocket endpoint for telemetry data streaming
    
    Args:
        websocket: Conexión WebSocket
        is_processor: Si es True, marca la conexión como procesador (recibe datos sin procesar)
                     Si es False, es un cliente normal (solo recibe datos procesados)
    
    Usage:
        Cliente normal: ws://localhost:8003/ws/telemetria
        Procesador: ws://localhost:8003/ws/telemetria?processor=true
    """
    await manager.connect(websocket, is_processor=is_processor)
    
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
        client_type = "procesador" if is_processor else "cliente"
        logger.info(f"{client_type.capitalize()} desconectado del WebSocket")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")
        manager.disconnect(websocket)
        await websocket.close()

