"""
Configuración de fixtures para pruebas WebSocket WS-MS-002
"""
import pytest
import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone


@pytest.fixture(scope="session")
def ws_config():
    """Configuración básica para tests WebSocket"""
    return {
        "simulator_host": os.getenv("SIMULATOR_HOST", "localhost"),
        "simulator_port": int(os.getenv("SIMULATOR_PORT", "8003")),
        "password": os.getenv("WEBSOCKET_PASSWORD", "telemetry_password_2024"),
        "timeout": 30,
        "imei_test": "357894561234567",
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def ws_url(ws_config):
    """Retorna la URL base del WebSocket"""
    host = ws_config["simulator_host"]
    port = ws_config["simulator_port"]
    return f"ws://{host}:{port}/ws/telemetria"


@pytest.fixture
def wss_url(ws_config):
    """Retorna la URL WSS (segura) del WebSocket"""
    host = ws_config["simulator_host"]
    port = ws_config["simulator_port"]
    return f"wss://{host}:{port}/ws/telemetria"


@pytest.fixture
def ws_password(ws_config):
    """Retorna la contraseña del WebSocket"""
    return ws_config["password"]


@pytest.fixture
def test_imei(ws_config):
    """Retorna el IMEI de prueba"""
    return ws_config["imei_test"]


@pytest.fixture
async def ws_connection_helper():
    """Helper para manejar conexiones WebSocket en tests"""
    import websockets
    
    connections = []
    
    async def connect(url: str, **kwargs):
        """Conecta al WebSocket y mantiene registro de la conexión"""
        conn = await websockets.connect(url, **kwargs)
        connections.append(conn)
        return conn
    
    yield connect
    
    # Cleanup: cerrar todas las conexiones abiertas
    for conn in connections:
        try:
            await conn.close()
        except:
            pass


@pytest.fixture
def sample_telemetry_packet(test_imei):
    """Paquete de telemetría de ejemplo para pruebas"""
    return {
        "imei": test_imei,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "ignition_status": 1,
            "movement_status": 1,
            "speed": 45.5,
            "gps_location": "+4.609710-74.081750/",
            "gsm_signal": 85,
            "rpm": 2500,
            "engine_temp": 85.0,
            "engine_load": 45.0,
            "oil_level": 75.0,
            "fuel_level": 60.0,
            "fuel_used_gps": 5.2,
            "instant_consumption": 8.5,
            "odometer_total": 12500.0,
            "odometer_trip": 150.0,
            "event_type": None,
            "event_g_value": None,
            "obd_faults": []
        }
    }


def pytest_configure(config):
    """Configuración global de pytest para WS-MS-002"""
    # Marcar tests como asyncio
    config.addinivalue_line(
        "markers", "websocket: mark test as websocket test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
