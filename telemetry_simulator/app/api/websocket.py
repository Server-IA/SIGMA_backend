"""
WebSocket endpoint for real-time telemetry data streaming
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.simulator.generator import TelemetryGenerator

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts telemetry data"""
    
    def __init__(self):
        """Initialize with empty connections list"""
        # Diccionario que mapea WebSocket -> request_id (None para procesadores)
        self.active_connections: Dict[WebSocket, Optional[str]] = {}
        self.processor_connections: List[WebSocket] = []  # Conexiones del procesador
        self.generator = TelemetryGenerator()
        self.is_running = False
        self.broadcast_task = None
        # Consumidores SSE: diccionario que mapea Queue -> request_id
        self._sse_consumers: Dict[asyncio.Queue, str] = {}
        # Timeout para conexiones sin datos (2 minutos = 120 segundos)
        self.data_timeout_seconds = int(os.getenv("WEBSOCKET_DATA_TIMEOUT", "120"))
        # Timestamp de último paquete recibido por conexión
        self.last_packet_time: Dict[WebSocket, datetime] = {}
        self.last_sse_packet_time: Dict[asyncio.Queue, datetime] = {}
        # Task para verificación de timeouts
        self._timeout_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket, is_processor: bool = False, request_id: Optional[str] = None):
        """Accept new WebSocket connection
        
        Args:
            websocket: Conexión WebSocket
            is_processor: Si es True, es una conexión del procesador (recibe datos sin procesar)
            request_id: ID de la solicitud para filtrar datos (obligatorio para clientes, None para procesadores)
        """
        if is_processor:
            await websocket.accept()
            self.processor_connections.append(websocket)
            logger.info(f"Conexión del procesador establecida. Total procesadores: {len(self.processor_connections)}")
        else:
            if request_id is None:
                await websocket.close(code=4003, reason="request_id es obligatorio para conexiones de clientes")
                return
            
            # Aceptar conexión y registrar (sin validar existencia - el timeout manejará si no hay datos)
            await websocket.accept()
            self.active_connections[websocket] = request_id
            self.last_packet_time[websocket] = datetime.now()
            
            # Enviar mensaje inicial de confirmación
            try:
                confirmation_msg = json.dumps({
                    "type": "connection_confirmed",
                    "request_id": request_id,
                    "message": f"Conexión establecida exitosamente para la solicitud '{request_id}'",
                    "status": "waiting_for_data",
                    "timeout_seconds": self.data_timeout_seconds
                })
                await websocket.send_text(confirmation_msg)
                logger.info(f"Nueva conexión WebSocket establecida para solicitud {request_id}. Total clientes: {len(self.active_connections)}")
            except Exception as e:
                logger.error(f"Error enviando mensaje de confirmación: {str(e)}")
        
        # Start data generation for processor if not already running
        if not self.is_running:
            await self._start_data_generation()
        
        # Iniciar verificación de timeouts si no está corriendo
        if not hasattr(self, '_timeout_task') or self._timeout_task is None or self._timeout_task.done():
            self._timeout_task = asyncio.create_task(self._check_timeouts())
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.processor_connections:
            self.processor_connections.remove(websocket)
            logger.info(f"Conexión del procesador cerrada. Total procesadores: {len(self.processor_connections)}")
        elif websocket in self.active_connections:
            request_id = self.active_connections.pop(websocket, None)
            self.last_packet_time.pop(websocket, None)
            logger.info(f"Conexión WebSocket cerrada para solicitud {request_id}. Total clientes: {len(self.active_connections)}")
        
        # Stop data generation if no processor connections
        if len(self.processor_connections) == 0 and self.is_running:
            self._stop_data_generation()
    
    async def _start_data_generation(self):
        """
        Inicia la generación de datos de telemetría simulada cada 5 segundos.
        """
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Iniciando generación de datos de telemetría simulada cada 5 segundos...")
        
        try:
            while self.is_running and len(self.processor_connections) > 0:
                # Generate new telemetry data
                telemetry_packet = self.generator.generate_response()
                telemetry_packet["is_real_data"] = False
                telemetry_packet["source"] = "simulator"
                
                # Log packet info
                imei = telemetry_packet.get("imei", "UNKNOWN")
                timestamp = telemetry_packet.get("timestamp", "UNKNOWN")
                logger.info(f"Generando paquete SIMULADO para procesador - IMEI: {imei}, TS: {timestamp}")
                
                # Convert to JSON
                message = json.dumps(telemetry_packet, default=str)
                
                # Send ONLY to processor connections
                await self._send_to_processors(message)
                
                # Wait 5 seconds before next transmission
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Error en generación de datos: {str(e)}")
        finally:
            self.is_running = False
            logger.info("Generación de datos detenida")
    
    def _stop_data_generation(self):
        """Stop the data generation loop"""
        self.is_running = False
        logger.info("Solicitud de detener generación de datos")
    
    def register_sse_consumer(self, queue: asyncio.Queue, request_id: str):
        """Registrar un consumidor SSE (cola) y devolver función para desuscribir
        
        Args:
            queue: Cola asyncio para recibir paquetes
            request_id: ID de la solicitud para filtrar datos (obligatorio)
        """
        self._sse_consumers[queue] = request_id
        self.last_sse_packet_time[queue] = datetime.now()

        def _unsubscribe():
            try:
                self._sse_consumers.pop(queue, None)
                self.last_sse_packet_time.pop(queue, None)
            except (ValueError, KeyError):
                pass

        return _unsubscribe

    async def _broadcast_sse(self, packet: dict):
        """Enviar paquete procesado solo a consumidores SSE que coincidan con el request_id del paquete"""
        if not self._sse_consumers:
            return

        packet_request_id = packet.get('request_id')
        if packet_request_id is None:
            logger.warning("Paquete sin request_id, no se envía a consumidores SSE")
            return

        dead_consumers: List[asyncio.Queue] = []
        for consumer, consumer_request_id in list(self._sse_consumers.items()):
            # Solo enviar si el request_id coincide
            if consumer_request_id == packet_request_id:
                try:
                    try:
                        consumer.put_nowait(packet)
                    except asyncio.QueueFull:
                        await consumer.put(packet)
                    # Actualizar timestamp de último paquete
                    self.last_sse_packet_time[consumer] = datetime.now()
                except Exception:
                    dead_consumers.append(consumer)

        for c in dead_consumers:
            try:
                self._sse_consumers.pop(c, None)
                self.last_sse_packet_time.pop(c, None)
            except (ValueError, KeyError):
                pass
    
    async def _check_timeouts(self):
        """Verifica conexiones sin datos y las cierra con mensaje de timeout"""
        while True:
            try:
                await asyncio.sleep(30)  # Verificar cada 30 segundos
                
                now = datetime.now()
                timeout_delta = timedelta(seconds=self.data_timeout_seconds)
                
                # Verificar WebSocket connections
                disconnected_ws = []
                for connection, request_id in list(self.active_connections.items()):
                    last_packet = self.last_packet_time.get(connection)
                    if last_packet:
                        time_since_last = now - last_packet
                        if time_since_last > timeout_delta:
                            try:
                                timeout_msg = json.dumps({
                                    "type": "timeout",
                                    "request_id": request_id,
                                    "message": f"No se han recibido datos para la solicitud '{request_id}' en {self.data_timeout_seconds} segundos. La conexión se cerrará.",
                                    "timeout_seconds": self.data_timeout_seconds,
                                    "reason": "no_data_received"
                                })
                                await connection.send_text(timeout_msg)
                                await connection.close(code=4005, reason=f"Timeout: No hay datos para la solicitud '{request_id}'")
                            except Exception as e:
                                logger.warning(f"Error cerrando conexión por timeout: {str(e)}")
                            disconnected_ws.append(connection)
                
                for conn in disconnected_ws:
                    self.disconnect(conn)
                
                # Verificar SSE consumers (enviar mensaje de timeout antes de remover)
                dead_sse = []
                for consumer, request_id in list(self._sse_consumers.items()):
                    last_packet = self.last_sse_packet_time.get(consumer)
                    if last_packet:
                        time_since_last = now - last_packet
                        if time_since_last > timeout_delta:
                            # Enviar mensaje de timeout antes de remover el consumidor
                            dead_sse.append((consumer, request_id))
                
                for consumer, request_id in dead_sse:
                    try:
                        # Enviar mensaje de timeout antes de remover el consumidor
                        timeout_packet = {
                            "type": "timeout",
                            "request_id": request_id,
                            "message": f"No se han recibido datos para la solicitud '{request_id}' en {self.data_timeout_seconds} segundos. La conexión se cerrará.",
                            "timeout_seconds": self.data_timeout_seconds,
                            "reason": "no_data_received"
                        }
                        try:
                            consumer.put_nowait(timeout_packet)
                        except asyncio.QueueFull:
                            # Si la cola está llena, intentar poner de forma asíncrona
                            await consumer.put(timeout_packet)
                        
                        # Ahora sí remover el consumidor
                        self._sse_consumers.pop(consumer, None)
                        self.last_sse_packet_time.pop(consumer, None)
                        logger.info(f"Consumidor SSE removido por timeout para solicitud {request_id}. Mensaje de timeout enviado.")
                    except (ValueError, KeyError):
                        pass
                    except Exception as e:
                        logger.warning(f"Error enviando mensaje de timeout a consumidor SSE: {str(e)}")
                        # Remover de todas formas si hay error
                        try:
                            self._sse_consumers.pop(consumer, None)
                            self.last_sse_packet_time.pop(consumer, None)
                        except (ValueError, KeyError):
                            pass
                        
            except Exception as e:
                logger.error(f"Error en verificación de timeouts: {str(e)}")

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
    
    async def _broadcast(self, packet: dict, message: str):
        """Send message only to clients that match the packet's request_id
        
        Args:
            packet: Diccionario con el paquete (debe incluir 'request_id')
            message: Mensaje JSON serializado a enviar
        """
        if not self.active_connections:
            return
        
        packet_request_id = packet.get('request_id')
        if packet_request_id is None:
            logger.warning("Paquete sin request_id, no se envía a clientes WebSocket")
            return
        
        # Broadcast solo a clientes que coincidan con el request_id
        disconnected = []
        for connection, conn_request_id in list(self.active_connections.items()):
            # Solo enviar si el request_id coincide
            if conn_request_id == packet_request_id:
                try:
                    await connection.send_text(message)
                    # Actualizar timestamp de último paquete
                    self.last_packet_time[connection] = datetime.now()
                except Exception as e:
                    logger.warning(f"Error enviando mensaje a cliente: {str(e)}")
                    disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_processed_packet(self, packet: dict):
        """
        Reenvía un paquete procesado con alertas agregadas solo a clientes que coincidan con el request_id
        
        Este es el ÚNICO método que envía datos a los clientes normales.
        Solo se llama cuando el TelemetryProcessor ha procesado los datos.
        
        Args:
            packet: Diccionario con el paquete de telemetría procesado (debe incluir 'request_id')
        """
        try:
            message = json.dumps(packet, default=str)
            packet_request_id = packet.get('request_id')
            
            # Contar clientes que coinciden con el request_id
            matching_clients = sum(1 for conn_request_id in self.active_connections.values() 
                                 if conn_request_id == packet_request_id)
            matching_sse = sum(1 for consumer_request_id in self._sse_consumers.values() 
                              if consumer_request_id == packet_request_id)
            
            # Enviar solo a clientes que coincidan con el request_id
            await self._broadcast(packet, message)
            # Enviar a consumidores SSE que coincidan con el request_id
            await self._broadcast_sse(packet)
            
            alerts_count = len(packet.get('alerts', [])) if packet.get('alerts') else 0
            imei = packet.get('imei', 'UNKNOWN')
            logger.info(
                f"Enviando paquete procesado (request_id={packet_request_id}) a WS:{matching_clients} cliente(s) y SSE:{matching_sse} consumidor(es) - IMEI: {imei}, Alertas: {alerts_count}"
            )
        except Exception as e:
            logger.error(f"Error reenviando paquete procesado: {str(e)}")


# Global connection manager instance
manager = ConnectionManager()


async def websocket_telemetry_endpoint(websocket: WebSocket, is_processor: bool = False, request_id: Optional[str] = None):
    """
    WebSocket endpoint for telemetry data streaming
    
    Args:
        websocket: Conexión WebSocket
        is_processor: Si es True, marca la conexión como procesador (recibe datos sin procesar)
                     Si es False, es un cliente normal (solo recibe datos procesados)
        request_id: ID de la solicitud para filtrar datos (obligatorio para clientes, None para procesadores)
    
    Usage:
        Cliente normal: ws://localhost:8003/ws/telemetria/{request_id}
        Procesador: ws://localhost:8003/ws/telemetria?processor=true
    """
    await manager.connect(websocket, is_processor=is_processor, request_id=request_id)
    
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

