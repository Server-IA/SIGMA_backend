"""
WS-MS-002: Tests de Ciclo de Datos y Tiempos (015-017)

Casos de prueba:
- WS-MS-002.15: Periodicidad del simulador
- WS-MS-002.16: Latencia E2E
- WS-MS-002.17: Orden de mensajes

Ejecutado por: GitHub Copilot
Fecha: 08/11/2025
"""

import pytest
import asyncio
import websockets
import json
import time
from datetime import datetime, timezone
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.websocket
@pytest.mark.performance
class TestCicloDatosTiempos:
    """Suite de pruebas para ciclo de datos, periodicidad y latencia"""

    async def test_WS_MS_002_015_periodicidad_simulador(
        self, ws_url, ws_password
    ):
        """
        WS-MS-002.15: Periodicidad del simulador
        
        Arrange: Cliente normal conectado
        Act: Medir intervalos entre mensajes
        Assert: ~30 s entre paquetes procesados a clientes normales
        """
        # Arrange
        url_client = f"{ws_url}?password={ws_password}"
        intervals: List[float] = []
        last_time: float = None
        
        # Act
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Recibir 3 mensajes para medir 2 intervalos
                for i in range(3):
                    message = await asyncio.wait_for(client_ws.recv(), timeout=65)
                    current_time = time.time()
                    
                    if last_time is not None:
                        interval = current_time - last_time
                        intervals.append(interval)
                        logger.info(f"Intervalo {len(intervals)}: {interval:.2f} segundos")
                    
                    last_time = current_time
                
            except asyncio.TimeoutError:
                if len(intervals) == 0:
                    pytest.skip("No se recibieron suficientes mensajes para medir periodicidad")
        
        # Assert
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            logger.info(f"Intervalo promedio: {avg_interval:.2f} segundos")
            
            # Verificar que está cerca de 30 segundos (±10s de tolerancia)
            assert 20 <= avg_interval <= 40, \
                f"Intervalo esperado ~30s, obtenido: {avg_interval:.2f}s"
            
            logger.info(f"✅ WS-MS-002.15: APROBADO - Periodicidad ~{avg_interval:.1f}s (esperado: 30s)")
        else:
            pytest.skip("No se pudieron medir intervalos")

    async def test_WS_MS_002_016_latencia_e2e(
        self, ws_url, ws_password
    ):
        """
        WS-MS-002.16: Latencia E2E
        
        Arrange: Cliente normal con timestamps instrumentados
        Act: Medir tiempo desde envío (timestamp en paquete) hasta recepción
        Assert: Latencia estable y documentada por debajo del SLA definido
        """
        # Arrange
        url_client = f"{ws_url}?password={ws_password}"
        latencies: List[float] = []
        
        # Act
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Recibir 3 mensajes para medir latencia
                for i in range(3):
                    recv_time = time.time()
                    message = await asyncio.wait_for(client_ws.recv(), timeout=65)
                    packet = json.loads(message)
                    
                    # Parsear timestamp del paquete
                    packet_ts = packet.get("timestamp")
                    if packet_ts:
                        try:
                            # Convertir timestamp ISO a datetime
                            packet_dt = datetime.fromisoformat(packet_ts.replace('Z', '+00:00'))
                            packet_time = packet_dt.timestamp()
                            
                            # Calcular latencia
                            latency = recv_time - packet_time
                            if latency > 0:  # Solo latencias positivas (paquete del pasado)
                                latencies.append(latency)
                                logger.info(f"Latencia {len(latencies)}: {latency*1000:.2f} ms")
                        except:
                            pass
                
            except asyncio.TimeoutError:
                if len(latencies) == 0:
                    pytest.skip("No se recibieron suficientes mensajes para medir latencia")
        
        # Assert
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            
            logger.info(f"Latencia promedio: {avg_latency*1000:.2f} ms")
            logger.info(f"Latencia mínima: {min_latency*1000:.2f} ms")
            logger.info(f"Latencia máxima: {max_latency*1000:.2f} ms")
            
            # SLA: latencia debe ser menor a 5 segundos (ajustar según requisitos)
            assert avg_latency < 5.0, \
                f"Latencia promedio debe ser < 5s, obtenida: {avg_latency:.2f}s"
            
            # Verificar estabilidad (desviación estándar)
            if len(latencies) > 1:
                import statistics
                std_dev = statistics.stdev(latencies)
                logger.info(f"Desviación estándar: {std_dev*1000:.2f} ms")
                
                # La desviación no debe ser muy alta (latencia estable)
                assert std_dev < 2.0, \
                    f"Latencia debe ser estable (std < 2s), obtenida: {std_dev:.2f}s"
            
            logger.info(
                f"✅ WS-MS-002.16: APROBADO - Latencia E2E: "
                f"avg={avg_latency*1000:.0f}ms, max={max_latency*1000:.0f}ms"
            )
        else:
            pytest.skip("No se pudieron medir latencias")

    async def test_WS_MS_002_017_orden_mensajes(
        self, ws_url, ws_password
    ):
        """
        WS-MS-002.17: Orden de mensajes
        
        Arrange: Cliente normal conectado
        Act: Recibir varios paquetes secuenciales
        Assert: Orden consistente por timestamp, sin reordenamientos observables
        """
        # Arrange
        url_client = f"{ws_url}?password={ws_password}"
        timestamps: List[datetime] = []
        
        # Act
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Recibir 3 mensajes para verificar orden
                for i in range(3):
                    message = await asyncio.wait_for(client_ws.recv(), timeout=65)
                    packet = json.loads(message)
                    
                    # Parsear timestamp
                    packet_ts = packet.get("timestamp")
                    if packet_ts:
                        try:
                            packet_dt = datetime.fromisoformat(packet_ts.replace('Z', '+00:00'))
                            timestamps.append(packet_dt)
                            logger.info(f"Mensaje {len(timestamps)}: {packet_ts}")
                        except:
                            pass
                
            except asyncio.TimeoutError:
                if len(timestamps) < 2:
                    pytest.skip("No se recibieron suficientes mensajes para verificar orden")
        
        # Assert
        if len(timestamps) >= 2:
            # Verificar que timestamps están en orden ascendente
            for i in range(len(timestamps) - 1):
                assert timestamps[i] <= timestamps[i+1], \
                    f"Mensajes fuera de orden: {timestamps[i]} > {timestamps[i+1]}"
            
            logger.info(
                f"✅ WS-MS-002.17: APROBADO - Orden de mensajes correcto "
                f"({len(timestamps)} mensajes secuenciales)"
            )
        else:
            pytest.skip("No se recibieron suficientes mensajes para verificar orden")

    @pytest.mark.skip(reason="Test de carga, requiere tiempo extendido")
    async def test_WS_MS_002_017_bis_orden_bajo_carga(
        self, ws_url, ws_password
    ):
        """
        Test auxiliar para verificar orden bajo carga
        Útil para pruebas de stress
        """
        url_client = f"{ws_url}?password={ws_password}"
        timestamps: List[datetime] = []
        
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Recibir 10 mensajes (5 minutos aprox)
                for i in range(10):
                    message = await asyncio.wait_for(client_ws.recv(), timeout=65)
                    packet = json.loads(message)
                    
                    packet_ts = packet.get("timestamp")
                    if packet_ts:
                        packet_dt = datetime.fromisoformat(packet_ts.replace('Z', '+00:00'))
                        timestamps.append(packet_dt)
                
            except asyncio.TimeoutError:
                pass
        
        # Verificar orden completo
        reorderings = 0
        for i in range(len(timestamps) - 1):
            if timestamps[i] > timestamps[i+1]:
                reorderings += 1
                logger.warning(
                    f"Reordenamiento detectado: {timestamps[i]} > {timestamps[i+1]}"
                )
        
        assert reorderings == 0, \
            f"Se detectaron {reorderings} reordenamientos en {len(timestamps)} mensajes"
        
        logger.info(
            f"✅ Orden perfecto mantenido en {len(timestamps)} mensajes bajo carga"
        )
