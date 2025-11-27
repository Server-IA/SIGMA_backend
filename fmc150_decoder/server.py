"""
Servidor socket para recibir datos del FMC150 y enviarlos al simulador
"""
import socket
import binascii
import json
import os
import requests
import logging
from datetime import datetime
from typing import Optional
import asyncio

from fmc150_decoder.decoder import decode_codec8e, hex_dump
from fmc150_decoder.adapter import convert_fmc150_to_telemetry_packet
from fmc150_decoder.websocket import ConnectionManager

logger = logging.getLogger(__name__)

# Configuración
HOST = os.getenv('FMC150_HOST', '0.0.0.0')
PORT = int(os.getenv('FMC150_PORT', '5055'))
SIMULATOR_URL = os.getenv('SIMULATOR_URL', 'http://telemetry_simulator:8000')

class FMC150Server:
    """Servidor para recibir y procesar datos del FMC150"""
    
    def __init__(self, ws_manager: ConnectionManager):
        self.ws_manager = ws_manager
        self.buffer_count = 0
        self.conexiones_imei = {}
        # Estado por conexión: handshake y buffer
        self.conn_state = {}  # {(ip, port): {"handshake_done": bool, "hs_buffer": bytearray(), "imei": str|None}}
        
    def process_buffer(self, data: bytes, device_imei: Optional[str] = None):
        """Procesa un buffer de datos AVL y lo transmite por WebSocket."""
        if not device_imei:
            logger.warning("⚠️ Buffer ignorado: IMEI no disponible todavía.")
            return
        try:
            hex_string = binascii.hexlify(data).decode('ascii')
            registros = decode_codec8e(hex_string, device_imei)
            logger.info(f"📦 Buffer #{self.buffer_count} decodificado - {len(registros)} registro(s)")
            for reg in registros:
                # Forzar IMEI en registro
                reg['imei'] = device_imei
                packet = convert_fmc150_to_telemetry_packet(reg, device_imei)
                # Usar asyncio para llamar a la corutina desde el hilo
                asyncio.run(self.ws_manager.broadcast_real_data(packet))
                logger.debug(f"📝 Registro procesado y enviado a broadcast - IMEI: {device_imei}, TS: {packet.get('timestamp')}")
        except Exception as e:
            logger.error(f"❌ Error procesando buffer: {e}", exc_info=True)
    
    def run(self):
        """Inicia el servidor socket"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        
        logger.info("=" * 80)
        logger.info("🔍 SERVIDOR DECODIFICADOR FMC150 - MODO INDEPENDIENTE")
        logger.info("=" * 80)
        logger.info(f"✅ Servidor TCP escuchando en {HOST}:{PORT}")
        logger.info(f"📡 Transmitiendo datos decodificados vía WebSocket...")
        logger.info(f"⏰ Esperando conexión del FMC150...\n")
        
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                logger.info("=" * 80)
                logger.info(f"📡 NUEVA CONEXIÓN desde {client_address[0]}:{client_address[1]}")
                logger.info(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("=" * 80)
                
                device_imei = None
                try:
                    while True:
                        data = client_socket.recv(4096)
                        if not data:
                            logger.info("\n❌ Conexión cerrada por el cliente")
                            break

                        # Estado de la conexión
                        if client_address not in self.conn_state:
                            self.conn_state[client_address] = {
                                "handshake_done": False,
                                "hs_buffer": bytearray(),
                                "imei": None
                            }
                        state = self.conn_state[client_address]

                        # Handshake pendiente
                        if not state["handshake_done"]:
                            state["hs_buffer"] += data
                            buf = state["hs_buffer"]
                            # Comienza correctamente
                            if buf.startswith(b'\x00\x0f'):
                                if len(buf) < 17:
                                    logger.debug(f"⏳ Handshake fragmentado acumulando ({len(buf)}/17 bytes)")
                                    continue
                                raw_imei = buf[2:17]
                                imei_candidate = raw_imei.decode('ascii', errors='ignore')
                                if len(imei_candidate) == 15 and imei_candidate.isdigit():
                                    state["imei"] = imei_candidate
                                    state["handshake_done"] = True
                                    self.conexiones_imei[client_address] = imei_candidate
                                    logger.info(f"\n{'═'*80}\n📱 IMEI HANDSHAKE: {imei_candidate}\n{'═'*80}")
                                    try:
                                        client_socket.send(b'\x01')
                                        logger.info("✅ ACK handshake enviado")
                                    except Exception as ack_e:
                                        logger.warning(f"⚠️ Error enviando ACK handshake: {ack_e}")
                                    remaining = buf[17:]
                                    state["hs_buffer"].clear()
                                    if remaining:
                                        self.buffer_count += 1
                                        logger.info(f"\n{'─'*80}\n📦 BUFFER #{self.buffer_count} (post-handshake)\n📱 IMEI: {state['imei']}\n{'─'*80}")
                                        logger.info(f"📊 Tamaño: {len(remaining)} bytes")
                                        logger.info(f"⏰ Recibido: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                                        self.process_buffer(remaining, state['imei'])
                                        try:
                                            client_socket.send(b'\x00\x00\x00\x01')
                                            logger.debug("✅ ACK datos enviado")
                                        except Exception as e_ack2:
                                            logger.warning(f"⚠️ Error enviando ACK datos: {e_ack2}")
                                        logger.info(f"\n{'─'*80}\n")
                                    continue
                                else:
                                    logger.warning(f"⚠️ IMEI inválido en handshake: '{imei_candidate}'")
                                    state["hs_buffer"].clear()
                                    continue
                            else:
                                # Bytes inesperados antes del handshake
                                if len(buf) >= 4 and buf.startswith(b'\x00\x00\x00\x00'):
                                    logger.warning("⚠️ Paquete AVL antes de handshake. Ignorado.")
                                    state["hs_buffer"].clear()
                                elif len(buf) > 32:
                                    logger.warning("⚠️ Bytes desconocidos antes de handshake. Limpieza.")
                                    state["hs_buffer"].clear()
                                continue

                        # Handshake ya hecho
                        device_imei = state["imei"]
                        self.buffer_count += 1
                        logger.info(f"\n{'─'*80}\n📦 BUFFER #{self.buffer_count}\n📱 IMEI: {device_imei}\n{'─'*80}")
                        logger.info(f"📊 Tamaño: {len(data)} bytes")
                        logger.info(f"⏰ Recibido: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                        self.process_buffer(data, device_imei)
                        try:
                            client_socket.send(b'\x00\x00\x00\x01')
                            logger.debug("✅ ACK datos enviado")
                        except Exception as e_ack:
                            logger.warning(f"⚠️ Error enviando ACK datos: {e_ack}")
                        logger.info(f"\n{'─'*80}\n")
                
                except Exception as e:
                    logger.error(f"\n❌ Error procesando datos: {e}", exc_info=True)
                finally:
                    client_socket.close()
                    logger.info(f"\n🔌 Conexión cerrada con {client_address[0]}:{client_address[1]}")
                    logger.info(f"📊 Total buffers recibidos: {self.buffer_count}\n")
        
        except KeyboardInterrupt:
            logger.info("\n\n⏹️  Servidor detenido por el usuario")
        except Exception as e:
            logger.error(f"\n❌ Error en el servidor: {e}", exc_info=True)
        finally:
            server_socket.close()
            logger.info(f"\n✅ Servidor cerrado")
            logger.info(f"📊 Total de buffers capturados: {self.buffer_count}")
            logger.info("=" * 80)

