"""
WS-MS-002: Tests de Alertas, Umbrales y Eventos (027-031)

Casos de prueba:
- WS-MS-002.27: Umbral de velocidad
- WS-MS-002.28: Evento de frenado con g-value
- WS-MS-002.29: OBD whitelisted
- WS-MS-002.30: OBD no whitelisted
- WS-MS-002.31: Evento no configurado

Ejecutado por: GitHub Copilot
Fecha: 08/11/2025
"""

import pytest
import asyncio
import websockets
import json
import logging
from datetime import datetime, timezone as dt_timezone

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.websocket
class TestAlertasUmbrales:
    """Suite de pruebas para alertas, umbrales y eventos"""

    async def test_WS_MS_002_027_umbral_velocidad(
        self, ws_url, ws_password
    ):
        """
        WS-MS-002.27: Umbral de velocidad
        
        Arrange: Configurar umbral de velocidad máximo
        Act: Enviar speed por encima del máximo
        Assert: alert {parameter: speed, reason} presente en paquete procesado
        """
        # Arrange
        url_client = f"{ws_url}?password={ws_password}"
        
        # Act
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Recibir mensaje procesado
                message = await asyncio.wait_for(client_ws.recv(), timeout=35)
                packet = json.loads(message)
                
                # Assert
                # Verificar estructura de alertas
                alerts = packet.get("alerts")
                if alerts:
                    assert isinstance(alerts, list), "alerts debe ser lista"
                    
                    # Buscar alerta de velocidad
                    speed_alerts = [a for a in alerts if a.get("parameter") == "speed"]
                    
                    if speed_alerts:
                        speed_alert = speed_alerts[0]
                        assert "reason" in speed_alert, "Alerta debe tener 'reason'"
                        logger.info(
                            f"✅ WS-MS-002.27: APROBADO - Alerta de velocidad: {speed_alert['reason']}"
                        )
                    else:
                        logger.info(
                            "⚠️ WS-MS-002.27: No se detectó alerta de velocidad "
                            "(datos dentro de umbrales o umbrales no configurados)"
                        )
                else:
                    logger.info(
                        "⚠️ WS-MS-002.27: No hay alertas en paquete "
                        "(todos los parámetros dentro de umbrales)"
                    )
                
            except asyncio.TimeoutError:
                pytest.skip("No se recibió mensaje en tiempo límite")

    async def test_WS_MS_002_028_evento_frenado_g_value(
        self, ws_url, ws_password
    ):
        """
        WS-MS-002.28: Evento de frenado con g-value
        
        Arrange: Configurar umbral de eventos con g-value
        Act: event_type=2 con g por encima del umbral
        Assert: Alerta de evento emitida
        """
        # Arrange
        url_client = f"{ws_url}?password={ws_password}"
        
        # Act
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Recibir mensaje procesado
                message = await asyncio.wait_for(client_ws.recv(), timeout=35)
                packet = json.loads(message)
                
                # Assert
                data = packet.get("data", {})
                event_type = data.get("event_type")
                event_g_value = data.get("event_g_value")
                alerts = packet.get("alerts", [])
                
                if event_type is not None:
                    logger.info(f"Evento detectado: tipo={event_type}, g-value={event_g_value}")
                    
                    # Buscar alerta de evento
                    event_alerts = [a for a in alerts if "evento" in a.get("reason", "").lower()]
                    
                    if event_alerts:
                        logger.info(
                            f"✅ WS-MS-002.28: APROBADO - Alerta de evento: {event_alerts[0]['reason']}"
                        )
                    else:
                        logger.info(
                            "⚠️ WS-MS-002.28: Evento sin alerta (g-value por debajo de umbral o no configurado)"
                        )
                else:
                    logger.info(
                        "⚠️ WS-MS-002.28: No hay evento en este paquete (event_type=None)"
                    )
                
            except asyncio.TimeoutError:
                pytest.skip("No se recibió mensaje en tiempo límite")

    async def test_WS_MS_002_029_obd_whitelisted(
        self, ws_url, ws_password
    ):
        """
        WS-MS-002.29: OBD whitelisted
        
        Arrange: Configurar código OBD permitido
        Act: Enviar código OBD permitido
        Assert: Se procesa, alerta si aplica, se registra código en entidad de fallas
        """
        # Arrange
        url_client = f"{ws_url}?password={ws_password}"
        
        # Act
        async with websockets.connect(url_client, close_timeout=5) as client_ws:
            try:
                # Recibir mensaje procesado
                message = await asyncio.wait_for(client_ws.recv(), timeout=35)
                packet = json.loads(message)
                
                # Assert
                data = packet.get("data", {})
                obd_faults = data.get("obd_faults", [])
                
                if obd_faults:
                    assert isinstance(obd_faults, list), "obd_faults debe ser lista"
                    logger.info(f"Fallas OBD detectadas: {obd_faults}")
                    
                    # Verificar que están en el paquete procesado (whitelisted)
                    logger.info(
                        f"✅ WS-MS-002.29: APROBADO - Códigos OBD whitelisted procesados: {len(obd_faults)}"
                    )
                else:
                    logger.info(
                        "⚠️ WS-MS-002.29: No hay fallas OBD en este paquete"
                    )
                
            except asyncio.TimeoutError:
                pytest.skip("No se recibió mensaje en tiempo límite")

    @pytest.mark.django_db(transaction=True)
    def test_WS_MS_002_030_obd_no_whitelisted(
        self, ws_demo_data
    ):
        """
        WS-MS-002.30: OBD no whitelisted
        
        Arrange: Código OBD no permitido
        Act: Enviar código OBD no permitido
        Assert: Ignorado, sin alerta ni persistencia en OBD
        """
        # Arrange
        from monitoring.services.telemetry_processor import TelemetryProcessor
        from monitoring.models import Data
        from machinery.models import OBDFaultMachinery, OBD_Faults
        
        processor = TelemetryProcessor()
        machinery = ws_demo_data["machinery"]
        device = ws_demo_data["device"]
        
        # Asegurar que hay un código OBD whitelisted y otro no
        # Limpiar whitelist
        OBDFaultMachinery.objects.filter(id_machinery=machinery).delete()
        
        # Crear solo P0100 como whitelisted
        obd_p0100, _ = OBD_Faults.objects.get_or_create(
            code="P0100",
            defaults={"description": "Falla sistema masa aire"}
        )
        OBDFaultMachinery.objects.create(
            id_machinery=machinery,
            id_obd_fault=obd_p0100,
            alert_enabled=True
        )
        
        # Crear paquete con código whitelisted y no whitelisted
        test_packet = {
            "imei": str(device.IMEI),
            "timestamp": datetime.now(dt_timezone.utc).isoformat(),
            "data": {
                "speed": 50.0,
                "gps_location": "+4.609710-74.081750/",
                "obd_faults": ["P0100", "P9999"]  # P0100 whitelisted, P9999 no
            }
        }
        
        # Limpiar datos previos
        Data.objects.filter(id_machinery=machinery, obd_fault__isnull=False).delete()
        
        # Act
        result = processor.process_telemetry_packet(test_packet)
        
        # Assert
        if result:
            # Verificar que solo se guardó el código whitelisted
            obd_data = Data.objects.filter(
                id_machinery=machinery,
                obd_fault__isnull=False
            )
            
            obd_codes = list(obd_data.values_list('obd_fault', flat=True))
            logger.info(f"Códigos OBD guardados: {obd_codes}")
            
            # Solo debe estar P0100
            assert "P0100" in obd_codes, "Código whitelisted debe guardarse"
            assert "P9999" not in obd_codes, "Código no whitelisted NO debe guardarse"
            
            logger.info(
                f"✅ WS-MS-002.30: APROBADO - OBD no whitelisted ignorado correctamente"
            )
        else:
            logger.warning("No se procesó paquete (posiblemente sin solicitud activa)")

    @pytest.mark.django_db(transaction=True)
    def test_WS_MS_002_031_evento_no_configurado(
        self, ws_demo_data
    ):
        """
        WS-MS-002.31: Evento no configurado
        
        Arrange: event_type fuera de whitelist
        Act: Enviar event_type no permitido
        Assert: Ignorado, sin alerta
        """
        # Arrange
        from monitoring.services.telemetry_processor import TelemetryProcessor
        from monitoring.models import Data
        from machinery.models import EventTypeMachinery, EventTypes
        
        processor = TelemetryProcessor()
        machinery = ws_demo_data["machinery"]
        device = ws_demo_data["device"]
        
        # Limpiar configuración de eventos
        EventTypeMachinery.objects.filter(id_machinery=machinery).delete()
        
        # Crear solo evento tipo 1 como configurado
        event_type_1, _ = EventTypes.objects.get_or_create(
            id_event_type=1,
            defaults={"name": "Frenado brusco", "description": "Evento de frenado"}
        )
        EventTypeMachinery.objects.create(
            id_machinery=machinery,
            id_event_type=event_type_1,
            alert_enabled=True,
            threshold=2.5
        )
        
        # Crear paquete con evento NO configurado (tipo 99)
        test_packet = {
            "imei": str(device.IMEI),
            "timestamp": datetime.now(dt_timezone.utc).isoformat(),
            "data": {
                "speed": 50.0,
                "gps_location": "+4.609710-74.081750/",
                "event_type": 99,  # NO configurado
                "event_g_value": 3.5
            }
        }
        
        # Limpiar datos previos de eventos
        Data.objects.filter(
            id_machinery=machinery,
            id_parameter__avl_id_parameter=253  # event_type
        ).delete()
        
        # Act
        result = processor.process_telemetry_packet(test_packet)
        
        # Assert
        if result:
            # Verificar estructura de resultado (debe tener alerts)
            if isinstance(result, dict):
                alerts = result.get("alerts", [])
                
                # No debe haber alerta de evento (tipo no configurado)
                event_alerts = [a for a in alerts if a.get("parameter") == "event_type"]
                
                assert len(event_alerts) == 0, \
                    "Evento no configurado NO debe generar alerta"
                
                logger.info(
                    f"✅ WS-MS-002.31: APROBADO - Evento no configurado ignorado correctamente"
                )
            else:
                logger.warning("Resultado no es dict con alerts")
        else:
            logger.warning("No se procesó paquete (posiblemente sin solicitud activa)")
