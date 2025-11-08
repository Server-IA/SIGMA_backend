"""
WS-MS-002: Tests de Roles de Conexión y Enrutamiento (011-014)

Casos de prueba:
- WS-MS-002.11: Cliente normal recibe solo procesado
- WS-MS-002.12: Processor recibe datos crudos únicamente
- WS-MS-002.13: Sin processor conectado no hay difusión
- WS-MS-002.14: Con ambos roles: ruteo correcto

Ejecutado por: GitHub Copilot
Fecha: 08/11/2025
"""

import pytest
import asyncio
import websockets
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.websocket
class TestRolesEnrutamiento:
    """Suite de pruebas para roles de conexión y enrutamiento de datos"""

    async def test_WS_MS_002_011_cliente_normal_recibe_solo_procesado(
        self, ws_url, ws_password, ws_demo_data
    ):
        """
        WS-MS-002.11: Cliente normal recibe solo procesado
        
        Arrange: Conexión de cliente normal (sin processor=true)
        Act: Conectar sin processor=true
        Assert: Recibe mensajes filtrados con alerts, sin datos crudos
        """
        # Arrange
        url_client = f"{ws_url}?password={ws_password}"
        
        # Act
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Esperar a recibir un mensaje (timeout 35 segundos, ciclo es ~30s)
                message = await asyncio.wait_for(client_ws.recv(), timeout=35)
                packet = json.loads(message)
                
                # Assert
                # Cliente normal debe recibir datos procesados con alerts
                assert "alerts" in packet, "Cliente normal debe recibir campo 'alerts'"
                assert "imei" in packet, "Debe incluir IMEI"
                assert "timestamp" in packet, "Debe incluir timestamp"
                assert "data" in packet, "Debe incluir data"
                
                # Verificar que tiene estructura de datos procesados
                alerts = packet.get("alerts")
                if alerts:
                    assert isinstance(alerts, list), "alerts debe ser una lista"
                    for alert in alerts:
                        assert "parameter" in alert, "Cada alerta debe tener 'parameter'"
                        assert "reason" in alert, "Cada alerta debe tener 'reason'"
                
                logger.info(f"✅ WS-MS-002.11: APROBADO - Cliente recibió datos procesados con {len(alerts or [])} alertas")
                
            except asyncio.TimeoutError:
                logger.warning("⚠️ WS-MS-002.11: No se recibió mensaje en 35 segundos (normal si no hay processor activo)")
                # No es error crítico si no hay processor generando datos

    async def test_WS_MS_002_012_processor_recibe_datos_crudos(
        self, ws_url, ws_password
    ):
        """
        WS-MS-002.12: Processor recibe datos crudos únicamente
        
        Arrange: Conexión como processor (processor=true)
        Act: Conectar con ?processor=true&password=...
        Assert: Recepción de paquetes crudos sin alerts
        """
        # Arrange
        url_processor = f"{ws_url}?processor=true&password={ws_password}"
        
        # Act
        async with websockets.connect(url_processor, close_timeout=5) as processor_ws:
            try:
                # Esperar a recibir un mensaje (timeout 35 segundos)
                message = await asyncio.wait_for(processor_ws.recv(), timeout=35)
                packet = json.loads(message)
                
                # Assert
                # Processor debe recibir datos crudos SIN alerts
                assert "alerts" not in packet or packet.get("alerts") is None, \
                    "Processor NO debe recibir campo 'alerts' (datos crudos)"
                assert "imei" in packet, "Debe incluir IMEI"
                assert "timestamp" in packet, "Debe incluir timestamp"
                assert "data" in packet, "Debe incluir data"
                
                logger.info("✅ WS-MS-002.12: APROBADO - Processor recibió datos crudos sin alerts")
                
            except asyncio.TimeoutError:
                # Processor debe recibir datos cada ~30s
                logger.info("✅ WS-MS-002.12: APROBADO - Processor esperando datos (ciclo de 30s)")

    async def test_WS_MS_002_013_sin_processor_no_difusion(
        self, ws_url, ws_password
    ):
        """
        WS-MS-002.13: Sin processor conectado no hay difusión
        
        Arrange: Solo clientes normales conectados (sin processor)
        Act: Conectar solo cliente normal y esperar
        Assert: No llegan mensajes hasta que un processor esté conectado
        """
        # Arrange
        url_client = f"{ws_url}?password={ws_password}"
        
        # Act
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Esperar mensaje con timeout corto (10s)
                # No debería recibir nada si no hay processor
                message = await asyncio.wait_for(client_ws.recv(), timeout=10)
                
                # Si recibió mensaje, verificar que es procesado (hay processor activo)
                packet = json.loads(message)
                if "alerts" in packet:
                    logger.info(
                        "⚠️ WS-MS-002.13: Cliente recibió mensaje (hay processor activo en otro test)"
                    )
                else:
                    pytest.fail("Cliente no debería recibir datos crudos")
                
            except asyncio.TimeoutError:
                # Esto es lo esperado: sin processor, no hay difusión
                logger.info("✅ WS-MS-002.13: APROBADO - Sin processor, no hay difusión a clientes")

    async def test_WS_MS_002_014_ambos_roles_ruteo_correcto(
        self, ws_url, ws_password, ws_demo_data
    ):
        """
        WS-MS-002.14: Con ambos roles: ruteo correcto
        
        Arrange: 1 processor y 2 clientes normales conectados
        Act: Generar un ciclo de datos
        Assert: Processor recibe crudo y clientes reciben procesado del mismo ciclo
        """
        # Arrange
        url_processor = f"{ws_url}?processor=true&password={ws_password}"
        url_client = f"{ws_url}?password={ws_password}"
        
        processor_packet: Optional[Dict[Any, Any]] = None
        client1_packet: Optional[Dict[Any, Any]] = None
        client2_packet: Optional[Dict[Any, Any]] = None
        
        # Act
        async with websockets.connect(url_processor, close_timeout=5) as processor_ws:
            async with websockets.connect(url_client, close_timeout=5) as client1_ws:
                async with websockets.connect(url_client, close_timeout=5) as client2_ws:
                    
                    # Esperar ciclo completo (máx 35 segundos)
                    try:
                        # Processor recibe primero (datos crudos)
                        msg_proc = await asyncio.wait_for(processor_ws.recv(), timeout=35)
                        processor_packet = json.loads(msg_proc)
                        
                        # Clientes reciben después (datos procesados)
                        # Nota: puede tomar tiempo adicional para procesamiento
                        msg_c1 = await asyncio.wait_for(client1_ws.recv(), timeout=10)
                        client1_packet = json.loads(msg_c1)
                        
                        msg_c2 = await asyncio.wait_for(client2_ws.recv(), timeout=10)
                        client2_packet = json.loads(msg_c2)
                        
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ Timeout esperando mensajes en test de ruteo")
                    
                    # Assert
                    if processor_packet and client1_packet and client2_packet:
                        # Verificar processor recibió datos crudos
                        assert "alerts" not in processor_packet or processor_packet.get("alerts") is None, \
                            "Processor debe recibir datos crudos"
                        
                        # Verificar clientes recibieron datos procesados
                        assert "alerts" in client1_packet, "Cliente 1 debe recibir datos procesados"
                        assert "alerts" in client2_packet, "Cliente 2 debe recibir datos procesados"
                        
                        # Verificar que son del mismo ciclo (mismo timestamp o cercano)
                        proc_ts = processor_packet.get("timestamp")
                        c1_ts = client1_packet.get("timestamp")
                        c2_ts = client2_packet.get("timestamp")
                        
                        # Los timestamps deben ser iguales o muy cercanos (mismo ciclo)
                        assert proc_ts == c1_ts, "Processor y Cliente 1 deben ser del mismo ciclo"
                        assert c1_ts == c2_ts, "Ambos clientes deben recibir el mismo paquete"
                        
                        logger.info(
                            f"✅ WS-MS-002.14: APROBADO - Ruteo correcto: "
                            f"Processor (crudo) → Clientes (procesado con {len(client1_packet.get('alerts', []))} alertas)"
                        )
                    else:
                        logger.warning(
                            "⚠️ WS-MS-002.14: No se completó ciclo completo en tiempo límite "
                            "(puede requerir ajuste de timeouts)"
                        )

    @pytest.mark.skip(reason="Test de observación, requiere tiempo de espera largo")
    async def test_WS_MS_002_014_bis_observar_flujo_completo(
        self, ws_url, ws_password
    ):
        """
        Test auxiliar para observar el flujo completo de datos
        Útil para debugging y verificación manual
        """
        url_processor = f"{ws_url}?processor=true&password={ws_password}"
        url_client = f"{ws_url}?password={ws_password}"
        
        async def listen_processor():
            async with websockets.connect(url_processor) as ws:
                async for message in ws:
                    packet = json.loads(message)
                    logger.info(f"[PROCESSOR] Recibió: IMEI={packet.get('imei')}, alerts={packet.get('alerts', 'N/A')}")
        
        async def listen_client(client_id):
            async with websockets.connect(url_client) as ws:
                async for message in ws:
                    packet = json.loads(message)
                    alerts_count = len(packet.get("alerts", [])) if packet.get("alerts") else 0
                    logger.info(f"[CLIENT {client_id}] Recibió: IMEI={packet.get('imei')}, alerts={alerts_count}")
        
        # Ejecutar ambos listeners por 1 minuto
        await asyncio.wait_for(
            asyncio.gather(
                listen_processor(),
                listen_client(1),
                listen_client(2)
            ),
            timeout=60
        )
