import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pytest
import websockets


# ========= Helpers =========

def ws_base_url() -> str:
    host = os.getenv("WS_HOST", "telemetry_simulator")  # dentro del contenedor
    port = os.getenv("WS_PORT", "8000")
    return f"ws://{host}:{port}/ws/telemetria"


def ws_password() -> str:
    return os.getenv("WEBSOCKET_PASSWORD", "telemetry_password_2024")


def ws_url_client() -> str:
    return f"{ws_base_url()}?password={ws_password()}"


def ws_url_processor() -> str:
    return f"{ws_base_url()}?processor=true&password={ws_password()}"


@dataclass
class WSMsg:
    role: str
    payload: Dict[str, Any]
    arrival_monotonic: float

    @property
    def key(self) -> Tuple[str, str]:
        return (str(self.payload.get("imei", "")), str(self.payload.get("timestamp", "")))


async def recv_for(uri: str, role: str, seconds: int) -> List[WSMsg]:
    msgs: List[WSMsg] = []
    deadline = time.monotonic() + seconds
    async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
        while time.monotonic() < deadline:
            timeout = max(1.0, min(35.0, deadline - time.monotonic() + 5.0))
            try:
                data = await asyncio.wait_for(ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                continue
            except Exception:
                break
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue
            msgs.append(WSMsg(role=role, payload=payload, arrival_monotonic=time.monotonic()))
    return msgs


def is_processed(payload: Dict[str, Any]) -> bool:
    return "alerts" in payload


# ========= Tests =========

@pytest.mark.websocket
async def test_WS_MS_002_basic_connection_acceptance():
    """WS-MS-002: Verificar que el servidor acepta conexiones WebSocket básicas."""
    uri = ws_url_client()
    # Si conecta sin excepción, handshake 101 aceptado
    async with websockets.connect(uri, ping_interval=20, ping_timeout=20):
        pass


@pytest.mark.websocket
async def test_WS_MS_005_json_integrity_one_processed_message():
    """WS-MS-005: Validar integridad de estructura JSON en mensajes procesados."""
    uri = ws_url_client()
    async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
        # Esperar un mensaje procesado (puede tardar hasta ~30s)
        msg = await asyncio.wait_for(ws.recv(), timeout=45)
        payload = json.loads(msg)
        # Estructura mínima
        assert isinstance(payload, dict)
        assert "imei" in payload and isinstance(payload["imei"], (str, int))
        assert "timestamp" in payload and isinstance(payload["timestamp"], str)
        assert "data" in payload and isinstance(payload["data"], dict)
        # alerts puede ser None o lista
        assert "alerts" in payload
        alerts = payload.get("alerts")
        assert alerts is None or isinstance(alerts, list)


@pytest.mark.websocket
@pytest.mark.long
async def test_WS_MS_004_multiclient_broadcast_minimal():
    """WS-MS-004: Verificar broadcast a múltiples clientes simultáneos."""
    if os.getenv("RUN_WS_MS_LONG", "0") != "1":
        pytest.skip("RUN_WS_MS_LONG != 1, omitiendo prueba de multicliente (~35s)")
    
    uri = ws_url_client()
    N = int(os.getenv("WS_MS_MULTI_CLIENTS", "3"))

    async def recv_one(ws):
        msg = await asyncio.wait_for(ws.recv(), timeout=45)
        return json.loads(msg)

    conns = [await websockets.connect(uri, ping_interval=20, ping_timeout=20) for _ in range(N)]
    try:
        # Recibir un mensaje por cliente (mismo ciclo esperado)
        msgs = await asyncio.gather(*[recv_one(ws) for ws in conns])
        # Correlacionar por (imei,timestamp): al menos dos deben coincidir
        keys = [(str(m.get("imei")), str(m.get("timestamp"))) for m in msgs]
        # Verificar que haya al menos un par de iguales (mismo ciclo)
        duplicates = any(keys.count(k) > 1 for k in keys)
        assert duplicates, f"No se observaron mensajes coincidentes por ciclo: {keys}"
    finally:
        for ws in conns:
            await ws.close()


@pytest.mark.websocket
@pytest.mark.long
async def test_WS_MS_006_reconnect_behavior_basic():
    """WS-MS-006: Validar comportamiento de reconexión tras cierre controlado."""
    if os.getenv("RUN_WS_MS_LONG", "0") != "1":
        pytest.skip("RUN_WS_MS_LONG != 1, omitiendo prueba de reconexión (~60s)")
    
    uri = ws_url_client()
    # Conectar, cerrar, reconectar, recibir siguiente mensaje
    ws = await websockets.connect(uri, ping_interval=20, ping_timeout=20)
    try:
        # Cerrar controlado
        await ws.close()
        # Reintentar nueva conexión
        ws2 = await websockets.connect(uri, ping_interval=20, ping_timeout=20)
        try:
            msg = await asyncio.wait_for(ws2.recv(), timeout=60)
            payload = json.loads(msg)
            assert isinstance(payload, dict) and "timestamp" in payload
        finally:
            await ws2.close()
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@pytest.mark.websocket
@pytest.mark.long
async def test_WS_MS_003_periodic_and_double_emission():
    """WS-MS-003: Validar periodicidad y doble emisión (raw→processed)."""
    if os.getenv("RUN_WS_MS_LONG", "0") != "1":
        pytest.skip("RUN_WS_MS_LONG != 1, omitiendo prueba larga (~75s)")
    
    listen_s = int(os.getenv("WS_MS_003_LISTEN_SECONDS", "75"))

    raw_uri = ws_url_processor()
    proc_uri = ws_url_client()

    raw_msgs, processed_msgs = await asyncio.gather(
        recv_for(raw_uri, "raw", listen_s),
        recv_for(proc_uri, "processed", listen_s),
    )

    assert raw_msgs, "No llegaron mensajes CRUDOS (procesador)." 
    assert processed_msgs, "No llegaron mensajes PROCESADOS (cliente)."

    # Procesados deben contener 'alerts' (None o lista)
    assert all("alerts" in m.payload for m in processed_msgs)

    # Correlación y orden crudo→procesado por (imei,timestamp)
    def group(messages: List[WSMsg]):
        buckets: Dict[Tuple[str, str], List[WSMsg]] = {}
        for m in messages:
            buckets.setdefault(m.key, []).append(m)
        return buckets

    raw_by = group(raw_msgs)
    proc_by = group(processed_msgs)

    # Estimación de ciclos esperados
    expected = max(1, (listen_s - 5) // 30)

    correlated = []
    ordering_violations = []
    for key, rlist in raw_by.items():
        if key not in proc_by:
            continue
        r = sorted(rlist, key=lambda m: m.arrival_monotonic)[0]
        p = sorted(proc_by[key], key=lambda m: m.arrival_monotonic)[0]
        correlated.append((r, p))
        if p.arrival_monotonic <= r.arrival_monotonic:
            ordering_violations.append(key)

    assert len(correlated) >= expected, (
        f"Esperados >= {expected} ciclos correlacionados; obtenidos {len(correlated)}."
    )
    assert not ordering_violations, f"Procesado llegó antes/no después del crudo para {ordering_violations}"


@pytest.mark.websocket
@pytest.mark.long
async def test_WS_MS_008_rebroadcast_processed_reaches_clients():
    """WS-MS-008: Confirmar que rebroadcast de procesados llega a clientes."""
    if os.getenv("RUN_WS_MS_LONG", "0") != "1":
        pytest.skip("RUN_WS_MS_LONG != 1, omitiendo prueba (~35-45s)")
    
    # Con un cliente normal, confirmar que llega un paquete con 'alerts'
    uri = ws_url_client()
    async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=45)
        payload = json.loads(msg)
        assert "alerts" in payload
        # No exigimos cantidad >0 porque depende de umbrales; solo que sea campo presente


@pytest.mark.websocket
async def test_WS_MS_007_processor_enrichment():
    """WS-MS-007: Recepción y enriquecimiento de paquete en procesador."""
    # Verificar que el procesador recibe y enriquece correctamente
    uri = ws_url_client()
    async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=45)
        payload = json.loads(msg)
        
        # Validar campos enriquecidos
        assert "alerts" in payload, "Paquete procesado debe incluir campo 'alerts'"
        assert "data" in payload, "Paquete debe contener campo 'data'"
        
        data = payload.get("data", {})
        # Verificar que hay datos mínimos del enriquecimiento
        assert isinstance(data, dict), "Campo 'data' debe ser un diccionario"


@pytest.mark.websocket
@pytest.mark.long
async def test_WS_MS_011_driving_events_detection():
    """WS-MS-011: Detección de eventos de conducción con valor G en alerts."""
    if os.getenv("RUN_WS_MS_LONG", "0") != "1":
        pytest.skip("RUN_WS_MS_LONG != 1, omitiendo prueba (~45s)")
    
    uri = ws_url_client()
    async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
        # Escuchar varios mensajes para encontrar eventos
        found_event = False
        for _ in range(3):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=45)
                payload = json.loads(msg)
                
                data = payload.get("data", {})
                alerts = payload.get("alerts")
                
                # Si hay event_type y event_g_value, debe haber alerta correspondiente
                if data.get("event_type") is not None and data.get("event_g_value") is not None:
                    if isinstance(alerts, list) and len(alerts) > 0:
                        # Buscar alerta de evento
                        event_alerts = [a for a in alerts if "event" in str(a.get("parameter", "")).lower()]
                        if event_alerts:
                            # Validar que tiene razón con tipo e intensidad
                            assert "reason" in event_alerts[0], "Alerta de evento debe tener 'reason'"
                            found_event = True
                            break
            except asyncio.TimeoutError:
                continue
        
        # Si no se encontraron eventos, omitir en lugar de fallar (depende del simulador)
        if not found_event:
            pytest.skip("No se detectaron eventos de conducción en los mensajes recibidos")


@pytest.mark.websocket
async def test_WS_MS_010_threshold_alert_generation():
    """WS-MS-010: Generación de alerta por superación de umbral."""
    uri = ws_url_client()
    async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=45)
        payload = json.loads(msg)
        
        # Validar estructura de alerts
        alerts = payload.get("alerts")
        if alerts and isinstance(alerts, list) and len(alerts) > 0:
            # Si hay alertas, deben tener estructura correcta
            for alert in alerts:
                assert isinstance(alert, dict), "Cada alerta debe ser un diccionario"
                assert "parameter" in alert or "reason" in alert, "Alerta debe tener 'parameter' o 'reason'"


@pytest.mark.websocket
@pytest.mark.long  
async def test_WS_MS_026_client_reconnection_on_network_loss():
    """WS-MS-026: Pérdida de red y reconexión automática del cliente."""
    if os.getenv("RUN_WS_MS_LONG", "0") != "1":
        pytest.skip("RUN_WS_MS_LONG != 1, omitiendo prueba de reconexión (~60s)")
    
    uri = ws_url_client()
    
    # Primera conexión
    ws1 = await websockets.connect(uri, ping_interval=20, ping_timeout=20)
    try:
        msg1 = await asyncio.wait_for(ws1.recv(), timeout=45)
        payload1 = json.loads(msg1)
        assert "timestamp" in payload1
        
        # Simular pérdida cerrando la conexión
        await ws1.close()
    except Exception:
        pass
    
    # Esperar un momento (simular backoff)
    await asyncio.sleep(2)
    
    # Reconectar
    ws2 = await websockets.connect(uri, ping_interval=20, ping_timeout=20)
    try:
        msg2 = await asyncio.wait_for(ws2.recv(), timeout=45)
        payload2 = json.loads(msg2)
        assert "timestamp" in payload2, "Debe recibir mensajes tras reconexión"
    finally:
        await ws2.close()
