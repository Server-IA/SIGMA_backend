# WS-MS-003 - WebSocket Telemetry Tests

## 📁 Estructura

```
test/WS-MS-003/
├── __init__.py              # Inicializador del paquete
├── WS-MS-003.py            # Suite completa de tests WebSocket
└── WS-MS-003-REPORT.md     # Reporte oficial de ejecución
```

## 🚀 Ejecución Rápida

### Tests rápidos (2 tests, ~15 segundos)
```bash
docker-compose exec web pytest -m "websocket and not long" test/WS-MS-003/
```

### Tests largos (4 tests, ~5 minutos)
```bash
docker-compose exec web sh -lc 'RUN_WS_MS_LONG=1 WS_HOST=telemetry_simulator WS_PORT=8000 pytest -m long test/WS-MS-003/'
```

### Todos los tests (10 tests, ~6 minutos)
```bash
docker-compose exec web sh -lc 'RUN_WS_MS_LONG=1 WS_HOST=telemetry_simulator WS_PORT=8000 pytest -v test/WS-MS-003/'
```

## 📊 Tests Incluidos

| ID | Descripción | Marker |
|---|---|---|
| WS-MS-002 | Conexión WebSocket básica | `websocket` |
| WS-MS-003 | Periodicidad y doble emisión | `websocket`, `long` |
| WS-MS-004 | Broadcast a múltiples clientes | `websocket`, `long` |
| WS-MS-005 | Integridad JSON | `websocket` |
| WS-MS-006 | Reconexión tras cierre | `websocket`, `long` |
| WS-MS-007 | Enriquecimiento del procesador | `websocket` |
| WS-MS-008 | Rebroadcast HTTP+WS | `websocket`, `long` |
| WS-MS-010 | Generación de alertas | `websocket` |
| WS-MS-011 | Eventos de conducción | `websocket`, `long` |
| WS-MS-026 | Reconexión automática | `websocket`, `long` |

## ⚙️ Variables de Entorno

| Variable | Default | Descripción |
|---|---|---|
| `RUN_WS_MS_LONG` | `0` | Habilitar tests largos (1=sí) |
| `WS_MS_003_LISTEN_SECONDS` | `75` | Duración de escucha WS-MS-003 |
| `WS_MS_MULTI_CLIENTS` | `3` | Clientes concurrentes WS-MS-004 |
| `WS_HOST` | `telemetry_simulator` | Host del WebSocket |
| `WS_PORT` | `8000` | Puerto del WebSocket |
| `WEBSOCKET_PASSWORD` | `telemetry_password_2024` | Password de autenticación |

## 📋 Requisitos Previos

1. Servicios activos:
   ```bash
   docker-compose up -d
   ```

2. Base de datos semillada:
   ```bash
   # Ejecutar script de seed
   docker-compose exec web python test/WS-MS-003/seed_data.py
   ```
   
   **Nota:** Los datos de prueba se crean automáticamente al ejecutar los tests gracias al fixture `ws_demo_data` en `test/conftest.py`.

## 📄 Reporte

Ver [WS-MS-003-REPORT.md](./WS-MS-003-REPORT.md) para el reporte completo de ejecución.

---

**Última ejecución:** 06/11/2025  
**Ejecutado por:** Nicolás Urrutia  
**Resultado:** ✅ 9 passed, 1 skipped (90% success rate)
