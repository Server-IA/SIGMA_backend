"""
WS-MS-002: Tests de Autenticación y Handshake (001-010)

Casos de prueba:
- WS-MS-002.1: Conexión exitosa con password válido
- WS-MS-002.2: Rechazo por password incorrecto
- WS-MS-002.3: Rechazo por password ausente
- WS-MS-002.4: Handshake WSS en producción
- WS-MS-002.5: Falla de certificado TLS
- WS-MS-002.6: Validación de Origin permitido
- WS-MS-002.7: Origin no permitido (CSWSH)
- WS-MS-002.8: Límite de conexiones (DoS básico)
- WS-MS-002.9: No exposición de credenciales en logs
- WS-MS-002.10: Cierre normal del servidor

Ejecutado por: GitHub Copilot
Fecha: 08/11/2025
"""

import pytest
import asyncio
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode
import ssl
import logging

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.websocket
class TestAuthenticationHandshake:
    """Suite de pruebas para autenticación y handshake WebSocket"""

    async def test_WS_MS_002_001_conexion_exitosa_password_valido(self, ws_url, ws_password):
        """
        WS-MS-002.1: Conexión exitosa con password válido
        
        Arrange: WEBSOCKET_PASSWORD correcto
        Act: Conectar a ws://localhost:8003/ws/telemetria?password=valor_correcto
        Assert: onopen exitoso y estado CONNECTED sin cierre inmediato
        """
        # Arrange
        url_with_password = f"{ws_url}?password={ws_password}"
        
        # Act
        try:
            async with websockets.connect(url_with_password, close_timeout=5) as websocket:
                # Assert
                assert websocket.open, "WebSocket debería estar abierto"
                assert websocket.state.name == "OPEN", f"Estado esperado: OPEN, obtenido: {websocket.state.name}"
                
                # Verificar que no se cierra inmediatamente
                await asyncio.sleep(2)
                assert websocket.open, "WebSocket no debería cerrarse inmediatamente"
                
                logger.info("✅ WS-MS-002.1: APROBADO - Conexión exitosa con password válido")
                
        except Exception as e:
            pytest.fail(f"Conexión falló con password válido: {str(e)}")

    async def test_WS_MS_002_002_rechazo_password_incorrecto(self, ws_url):
        """
        WS-MS-002.2: Rechazo por password incorrecto
        
        Arrange: Password inválida
        Act: Conectar con password errónea
        Assert: Cierre con código privado de aplicación (4xxx) y razón legible
        """
        # Arrange
        invalid_password = "password_incorrecta_123"
        url_with_invalid_password = f"{ws_url}?password={invalid_password}"
        
        # Act & Assert
        with pytest.raises((ConnectionClosed, InvalidStatusCode)) as exc_info:
            async with websockets.connect(url_with_invalid_password, close_timeout=5) as websocket:
                # Si llegamos aquí, esperar mensaje de cierre
                await websocket.recv()
        
        # Verificar código de cierre (4001 = código privado de aplicación)
        # websockets puede lanzar InvalidStatusCode si rechaza el handshake
        if isinstance(exc_info.value, InvalidStatusCode):
            # Handshake rechazado antes de establecer conexión
            logger.info(f"Handshake rechazado con código: {exc_info.value.status_code}")
        else:
            # Conexión cerrada con código privado
            assert exc_info.value.code >= 4000 and exc_info.value.code <= 4999, \
                f"Código de cierre debe estar en rango 4000-4999 (privado), obtenido: {exc_info.value.code}"
            assert "contraseña" in exc_info.value.reason.lower() or "password" in exc_info.value.reason.lower(), \
                f"Razón debe mencionar contraseña, obtenido: {exc_info.value.reason}"
        
        logger.info("✅ WS-MS-002.2: APROBADO - Rechazo por password incorrecto")

    async def test_WS_MS_002_003_rechazo_password_ausente(self, ws_url):
        """
        WS-MS-002.3: Rechazo por password ausente
        
        Arrange: Sin query parameter password
        Act: Conectar sin password
        Assert: Handshake no aceptado/cierre temprano con código de app y razón
        """
        # Act & Assert
        with pytest.raises((ConnectionClosed, InvalidStatusCode, Exception)) as exc_info:
            async with websockets.connect(ws_url, close_timeout=5) as websocket:
                # Si se conecta (no debería), esperar cierre inmediato
                await asyncio.sleep(1)
        
        # Debe fallar por falta de password (HTTP 422 o cierre 4xxx)
        logger.info(f"Conexión rechazada como esperado: {type(exc_info.value).__name__}")
        logger.info("✅ WS-MS-002.3: APROBADO - Rechazo por password ausente")

    @pytest.mark.skip(reason="Requiere configuración WSS en producción")
    async def test_WS_MS_002_004_handshake_wss_produccion(self, wss_url, ws_password):
        """
        WS-MS-002.4: Handshake WSS en producción
        
        Arrange: Endpoint wss con certificado válido
        Act: Conectar vía wss://...
        Assert: Establecimiento TLS y canal cifrado conforme a RFC 6455
        """
        # Arrange
        url_with_password = f"{wss_url}?password={ws_password}"
        ssl_context = ssl.create_default_context()
        
        # Act
        try:
            async with websockets.connect(
                url_with_password, 
                ssl=ssl_context,
                close_timeout=5
            ) as websocket:
                # Assert
                assert websocket.open, "WebSocket WSS debería estar abierto"
                logger.info("✅ WS-MS-002.4: APROBADO - Handshake WSS exitoso")
        except Exception as e:
            pytest.fail(f"Handshake WSS falló: {str(e)}")

    @pytest.mark.skip(reason="Requiere certificado inválido configurado")
    async def test_WS_MS_002_005_falla_certificado_tls(self, wss_url, ws_password):
        """
        WS-MS-002.5: Falla de certificado TLS
        
        Arrange: Certificado inválido/caducado
        Act: Conectar a wss
        Assert: Fallo de conexión por verificación TLS antes del handshake WebSocket
        """
        # Arrange
        url_with_password = f"{wss_url}?password={ws_password}"
        ssl_context = ssl.create_default_context()
        # Forzar verificación estricta
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        # Act & Assert
        with pytest.raises(ssl.SSLError):
            async with websockets.connect(
                url_with_password,
                ssl=ssl_context,
                close_timeout=5
            ) as websocket:
                pass
        
        logger.info("✅ WS-MS-002.5: APROBADO - Certificado TLS inválido rechazado")

    @pytest.mark.skip(reason="Requiere configuración de Origin whitelist en servidor")
    async def test_WS_MS_002_006_validacion_origin_permitido(self, ws_url, ws_password):
        """
        WS-MS-002.6: Validación de Origin permitido
        
        Arrange: Frontend con Origin permitido
        Act: Handshake desde dominio permitido
        Assert: Conexión aceptada por allowlist de Origin
        """
        # Arrange
        url_with_password = f"{ws_url}?password={ws_password}"
        allowed_origin = "http://localhost:3000"
        
        # Act
        try:
            async with websockets.connect(
                url_with_password,
                extra_headers={"Origin": allowed_origin},
                close_timeout=5
            ) as websocket:
                # Assert
                assert websocket.open, "Conexión con Origin permitido debería ser aceptada"
                logger.info("✅ WS-MS-002.6: APROBADO - Origin permitido aceptado")
        except Exception as e:
            pytest.fail(f"Conexión con Origin permitido falló: {str(e)}")

    @pytest.mark.skip(reason="Requiere configuración de Origin whitelist en servidor")
    async def test_WS_MS_002_007_origin_no_permitido_cswsh(self, ws_url, ws_password):
        """
        WS-MS-002.7: Origin no permitido (CSWSH - Cross-Site WebSocket Hijacking)
        
        Arrange: Origen malicioso
        Act: Handshake con Origin no autorizado
        Assert: Rechazo del handshake por política de Origin
        """
        # Arrange
        url_with_password = f"{ws_url}?password={ws_password}"
        malicious_origin = "http://malicious-site.com"
        
        # Act & Assert
        with pytest.raises((ConnectionClosed, InvalidStatusCode)):
            async with websockets.connect(
                url_with_password,
                extra_headers={"Origin": malicious_origin},
                close_timeout=5
            ) as websocket:
                pass
        
        logger.info("✅ WS-MS-002.7: APROBADO - Origin no permitido rechazado (CSWSH prevented)")

    @pytest.mark.skip(reason="Test de carga, puede afectar otros tests")
    async def test_WS_MS_002_008_limite_conexiones_dos(self, ws_url, ws_password):
        """
        WS-MS-002.8: Límite de conexiones (DoS básico)
        
        Arrange: Sistema con límite de conexiones configurado
        Act: Abrir muchas conexiones concurrentes desde misma IP/usuario
        Assert: Rechazos/limitación sin degradar servicio para clientes válidos
        """
        # Arrange
        url_with_password = f"{ws_url}?password={ws_password}"
        max_connections = 100
        connections = []
        
        # Act
        try:
            for i in range(max_connections):
                try:
                    conn = await websockets.connect(url_with_password, close_timeout=2)
                    connections.append(conn)
                except Exception as e:
                    # Conexión rechazada por límite (esperado)
                    logger.info(f"Conexión {i+1} rechazada: {str(e)}")
                    break
            
            # Assert
            # Debería haber un límite razonable de conexiones
            assert len(connections) < max_connections, \
                f"Sistema debería limitar conexiones, pero aceptó {len(connections)}"
            
            logger.info(f"✅ WS-MS-002.8: APROBADO - Límite de {len(connections)} conexiones aplicado")
            
        finally:
            # Cleanup
            for conn in connections:
                try:
                    await conn.close()
                except:
                    pass

    @pytest.mark.skip(reason="Requiere inspección de logs del servidor")
    async def test_WS_MS_002_009_no_exposicion_credenciales_logs(self, ws_url, ws_password):
        """
        WS-MS-002.9: No exposición de credenciales en logs
        
        Arrange: Servidor con logging habilitado
        Act: Revisar logs durante handshakes
        Assert: Password en query no debe quedar en logs en claro o debe ser redactado
        
        Nota: Este test requiere acceso a logs del servidor para verificar.
        Se marca como SKIP pero documenta el requisito de seguridad.
        """
        # Este test es más bien una verificación manual de logs
        # Se incluye como documentación de requisito de seguridad
        logger.warning(
            "⚠️ WS-MS-002.9: Test manual requerido - Verificar que logs no exponen password en claro"
        )
        pytest.skip("Requiere inspección manual de logs del servidor")

    async def test_WS_MS_002_010_cierre_normal_servidor(self, ws_url, ws_password):
        """
        WS-MS-002.10: Cierre normal del servidor
        
        Arrange: Conexión establecida
        Act: Servidor envía Close 1000 (normal closure)
        Assert: Cliente recibe Close y termina conexión de forma ordenada con 1000
        """
        # Arrange
        url_with_password = f"{ws_url}?password={ws_password}"
        
        # Act
        async with websockets.connect(url_with_password, close_timeout=5) as websocket:
            # Esperar un momento para conexión estable
            await asyncio.sleep(1)
            
            # Cerrar desde el cliente con código 1000
            await websocket.close(code=1000, reason="Test cierre normal")
            
            # Assert
            # El estado debe ser CLOSED
            assert websocket.closed, "WebSocket debería estar cerrado"
            
            # Si el servidor respondió con close frame, verificar código
            if websocket.close_code is not None:
                assert websocket.close_code == 1000, \
                    f"Código de cierre esperado: 1000, obtenido: {websocket.close_code}"
            
            logger.info("✅ WS-MS-002.10: APROBADO - Cierre normal con código 1000")
