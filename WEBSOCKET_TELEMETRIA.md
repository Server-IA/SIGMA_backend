# 📡 WebSocket de Telemetría

## 🔌 Conexión

**Endpoint:** `ws://localhost:8003/ws/telemetria`  
**Protocolo:** WebSocket (WSS en producción)  
**Frecuencia:** Cada ~30 segundos automáticamente (después del procesamiento)

**⚠️ REQUISITO:** Contraseña obligatoria para conectarse

**Variable de Entorno:** `WEBSOCKET_PASSWORD=telemetry_password_2024`

**URL de Conexión:**
```
ws://localhost:8003/ws/telemetria?password=telemetry_password_2024
```

**Parámetros de Query:**
- `password` (REQUERIDO): Contraseña para autenticarse. Debe coincidir con `WEBSOCKET_PASSWORD`
- `processor` (OPCIONAL): Si es `true`, marca la conexión como procesador (recibe datos sin procesar)

> **ℹ️ Nota:** 
> - **Clientes normales:** Solo reciben datos procesados con alertas
> - **Procesadores:** Se conectan con `?processor=true&password=...` y reciben datos sin procesar
> - Si la contraseña es incorrecta, la conexión se rechaza con código `4001`

---

## 📤 Formato de Datos

Cada mensaje es un JSON con esta estructura:

```json
{
  "imei": "352099001761481",
  "timestamp": "2025-11-05T10:00:00.123456-05:00",
  "data": {
    "ignition_status": 1,        // 0=OFF, 1=ON (solo si está configurado)
    "movement_status": 1,        // 0=Detenido, 1=Moviéndose (solo si está configurado)
    "speed": 120,                // km/h (0-350) (solo si está configurado)
    "gps_location": "+04.60971-074.08175/", // (solo si está configurado)
    "gsm_signal": 4,             // 1-5 (1=Excelente, 5=Pérdida) (solo si está configurado)
    "rpm": 2500,                 // (solo si está configurado)
    "engine_temp": 92,           // °C (solo si está configurado)
    "engine_load": 57,           // % (solo si está configurado)
    "oil_level": 80,             // % (solo si está configurado)
    "fuel_level": 68,            // % (solo si está configurado)
    "fuel_used_gps": 153.2,      // Litros (solo si está configurado)
    "instant_consumption": 14.5, // L/h (solo si está configurado)
    "obd_faults": ["P0135", "P0420"], // Array de códigos OBD (solo si está configurado)
    "odometer_total": 2456789,   // Metros (solo si está configurado)
    "odometer_trip": 34567,      // Metros (solo si está configurado)
    "event_type": 2,             // 1=Aceleración, 2=Frenado, 3=Curva (opcional)
    "event_g_value": 45          // Valor G del evento (opcional)
  },
  "alerts": [                    // null si no hay alertas, o array con alertas
    {
      "parameter": "speed",
      "reason": "Valor por encima del máximo configurado"
    }
  ]
}
```

**⚠️ IMPORTANTE - Filtrado de Parámetros:**
- Solo recibirás los parámetros que están configurados para el dispositivo específico
- Los parámetros no configurados en `telemetry_device_parameter` NO aparecerán en el JSON
- El frontend debe verificar la existencia de campos antes de usarlos: `if (data.data.speed !== undefined)`

---

## 🔐 Validación de Contraseña

**Antes de conectarse:**
1. El cliente debe incluir `password` como query parameter
2. El servidor valida que la contraseña coincida con `WEBSOCKET_PASSWORD`
3. Si es correcta: acepta la conexión
4. Si es incorrecta: rechaza con código `4001` y razón "Contraseña incorrecta"

**Configuración:**
```bash
# Variable de entorno requerida
WEBSOCKET_PASSWORD=telemetry_password_2024
```

---

## 🔄 Flujo del Sistema (Actualizado)

**1. Cliente se conecta** → `ws://localhost:8003/ws/telemetria?password=...`

**2. Validación de contraseña:**
   - Servidor valida `password` contra `WEBSOCKET_PASSWORD`
   - Si es incorrecta → Cierra conexión (código 4001)
   - Si es correcta → Acepta conexión

**3. Clasificación de conexión:**
   - Si `processor=true` → Va a lista `processor_connections` (solo procesador)
   - Si `processor=false` o no existe → Va a lista `active_connections` (clientes normales)

**4. Generación de datos (solo si hay procesador conectado):**
   - Simulador genera datos cada 30 segundos
   - **Envía SOLO al TelemetryProcessor** (no a clientes normales)

**5. Procesador Django recibe y procesa:**
   - Valida que no sea duplicado (cache de paquetes)
   - Valida solicitud de servicio activa (estados 20 o 21)
   - Valida fechas y estados logísticos
   - Valida parámetros configurados para el dispositivo
   - Valida eventos OBD y tipos de evento según whitelist
   - Verifica umbrales y genera alertas
   - Calcula estado logístico (Ida/Vuelta/Trabajo)
   - Guarda en tabla `data` solo parámetros configurados
   - Filtra parámetros antes de enviar

**6. Procesador envía paquete procesado** → HTTP POST a `http://simulator:8000/api/broadcast-processed`
   - El paquete incluye campo `alerts`
   - El paquete está filtrado (solo parámetros configurados)

**7. Simulador reenvía** → Reenvía el paquete procesado con alertas **SOLO a clientes normales**

**8. Cliente recibe** → Paquete procesado con alertas y parámetros filtrados

**🔑 Diferencia Clave:**
- **Clientes normales:** Reciben SOLO datos procesados (con alertas y filtrados)
- **Procesador:** Recibe SOLO datos sin procesar (para procesarlos)

---

## ⚙️ Validaciones y Condiciones

### Validación de Contraseña
- ✅ Contraseña requerida en query parameter
- ✅ Debe coincidir exactamente con `WEBSOCKET_PASSWORD`
- ❌ Sin contraseña → Conexión rechazada
- ❌ Contraseña incorrecta → Conexión rechazada (código 4001)

### Validación de Solicitudes de Servicio
- ✅ Solo procesa si hay solicitud activa (estados 20 o 21)
- ✅ Estado 20: Solo válido el día de inicio (`scheduled_start_date`)
- ✅ Estado 21: Válido dentro del rango completo (`scheduled_start_date` a `scheduled_end_date`)
- ✅ Estado 21: También válido FUERA del rango
- ❌ Estado 22 (Finalizada): NO se almacenan datos
- 🔄 Cache se refresca cada 4 paquetes para detectar cambios de estado

### Validación de Parámetros por Dispositivo
- ✅ Solo se almacenan parámetros configurados en `telemetry_device_parameter`
- ✅ Solo se envían por WebSocket parámetros configurados
- ✅ Parámetros no configurados se filtran antes de enviar
- ✅ Validación basada en `avl_id_parameter`

### Validación de Eventos OBD
- ✅ Solo se procesan códigos OBD presentes en `obd_fault_machinery` con `alert_enabled=true`
- ✅ Códigos no whitelisted se ignoran
- ✅ El campo `data` se guarda como `NULL`, solo se guarda el código en `obd_fault`

### Validación de Tipos de Evento
- ✅ Solo se procesan eventos configurados en `event_type_machinery`
- ✅ Se valida umbral configurado en `event_type_machinery`
- ✅ Eventos no configurados se ignoran

### Prevención de Duplicados
- ✅ Cache de paquetes procesados (identificador: `IMEI_timestamp`)
- ✅ Paquetes ya procesados se ignoran
- ✅ Cache se limpia automáticamente (entradas mayores a 5 minutos)

---

## ⚠️ Sistema de Alertas

Las alertas se generan cuando:

* **Valores fuera de umbral:** Parámetro supera límites configurados en `tolerance_thresholds`
* **Eventos detectados:** Cuando `event_type` y `event_g_value` no son null y cumplen condiciones
* **Solo para parámetros configurados:** No se generan alertas para parámetros no configurados

**Estructura:**
```json
{
  "parameter": "speed",
  "reason": "Valor por encima del máximo configurado"
}
```

> **⚠️ El campo `alerts` puede ser:** `null` (sin alertas), `[]` (vacío), o `[{...}]` (con alertas)

---

## 🚀 Ventajas

* ✅ **Tiempo real:** Datos cada ~30 segundos (después del procesamiento)
* ✅ **Escalable:** Múltiples clientes simultáneos
* ✅ **Alertas integradas:** En el mismo mensaje
* ✅ **Sin duplicados:** Cache previene reprocesamiento
* ✅ **Persistencia:** Todo guardado en BD
* ✅ **Seguridad:** Contraseña requerida para conectarse
* ✅ **Filtrado inteligente:** Solo parámetros configurados se envían
* ✅ **Datos procesados:** Clientes reciben solo datos validados y con alertas

---

## ⚠️ Consideraciones

* **Contraseña requerida:** No se puede conectar sin contraseña válida
* **WebSocket se cierra automáticamente** si no hay clientes conectados
* **Reconexión:** Solo recibe próximos paquetes (no históricos)
* **Un solo mensaje por paquete:** Los clientes reciben solo datos procesados (sin duplicados)
* **Producción:** Usar `wss://` (WebSocket seguro) sobre HTTPS
* **Parámetros opcionales:** El frontend debe verificar existencia de campos antes de usarlos
* **Contraseña en URL:** La contraseña va en la URL como query parameter (considerar seguridad en producción)

---

## 📝 Ejemplos de Uso

### JavaScript/React
```javascript
const password = 'telemetry_password_2024';
const ws = new WebSocket(`ws://localhost:8003/ws/telemetria?password=${password}`);

ws.onopen = () => {
    console.log('Conectado y autenticado');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Verificar existencia de campos antes de usar
    if (data.data.speed !== undefined) {
        console.log('Velocidad:', data.data.speed);
    }
    if (data.data.engine_temp !== undefined) {
        console.log('Temperatura:', data.data.engine_temp);
    }
    if (data.alerts && data.alerts.length > 0) {
        console.log('Alertas:', data.alerts);
    }
};

ws.onclose = (event) => {
    if (event.code === 4001) {
        console.error('Contraseña incorrecta');
    }
};

ws.onerror = (error) => {
    console.error('Error en WebSocket:', error);
};
```

### Postman
```
URL: ws://localhost:8003/ws/telemetria?password=telemetry_password_2024
```

Pasos:
1. Crear nueva solicitud WebSocket
2. Ingresar URL con contraseña
3. Clic en Connect
4. Esperar mensajes automáticos cada ~30 segundos

### HTML/JavaScript Simple
```html
<!DOCTYPE html>
<html>
<head>
    <title>Telemetry WebSocket Client</title>
</head>
<body>
    <input type="password" id="password" placeholder="Contraseña" value="telemetry_password_2024">
    <button onclick="connect()">Conectar</button>
    <div id="messages"></div>

    <script>
        let ws = null;
        
        function connect() {
            const password = document.getElementById('password').value;
            ws = new WebSocket(`ws://localhost:8003/ws/telemetria?password=${password}`);
            
            ws.onopen = () => {
                console.log('Conectado');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                document.getElementById('messages').innerHTML = 
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            };
            
            ws.onclose = (event) => {
                if (event.code === 4001) {
                    alert('Contraseña incorrecta');
                }
            };
        }
    </script>
</body>
</html>
```

---

## 🔧 Configuración Requerida

### Variable de Entorno
```bash
WEBSOCKET_PASSWORD=telemetry_password_2024
```

Esta variable debe estar configurada en:
- Servicio `simulator` (FastAPI)
- Servicio `telemetry_processor` (Django)

### Docker Compose
```yaml
simulator:
  environment:
    WEBSOCKET_PASSWORD: ${WEBSOCKET_PASSWORD}

telemetry_processor:
  environment:
    WEBSOCKET_PASSWORD: ${WEBSOCKET_PASSWORD}
```

### Archivo .env
```bash
# Contraseña para conectarse al WebSocket
WEBSOCKET_PASSWORD=telemetry_password_2024
```

---

## 📊 Tipos de Conexión

### Cliente Normal
- **URL:** `ws://localhost:8003/ws/telemetria?password=...`
- **Recibe:** Solo datos procesados con alertas y parámetros filtrados
- **Frecuencia:** Cada ~30 segundos (después del procesamiento)
- **Uso:** Dashboards, aplicaciones móviles, visualizadores

### Procesador
- **URL:** `ws://localhost:8003/ws/telemetria?processor=true&password=...`
- **Recibe:** Datos sin procesar para procesarlos y generar alertas
- **Frecuencia:** Cada 30 segundos (generación automática)
- **Uso:** Solo para el servicio `TelemetryProcessor` (Django)

---

## 🔍 Troubleshooting

### Error: Contraseña incorrecta (código 4001)
- ✅ Verificar que `WEBSOCKET_PASSWORD` esté configurada en `.env`
- ✅ Verificar que la contraseña en la URL coincida exactamente
- ✅ Verificar que no haya espacios adicionales en la contraseña
- ✅ Verificar logs del simulador para confirmar el rechazo

### No recibo mensajes
- ✅ Verificar que el TelemetryProcessor esté corriendo (necesario para generar datos procesados)
- ✅ Esperar ~30 segundos después de conectarse (los datos se generan cada 30 segundos)
- ✅ Verificar logs del simulador y procesador
- ✅ Verificar que haya al menos un procesador conectado

### Campos faltantes en los datos
- ✅ Verificar configuración en `telemetry_device_parameter` para el IMEI específico
- ✅ Solo parámetros configurados aparecen en el JSON
- ✅ Esto es normal y esperado según la configuración del dispositivo

### Datos no se guardan en BD
- ✅ Verificar que haya solicitud activa (estados 20 o 21)
- ✅ Verificar que la fecha del paquete esté dentro del rango válido
- ✅ Verificar logs del procesador para más detalles
- ✅ Verificar que el estado de la solicitud no sea 22 (Finalizada)

### Error de conexión en Postman
- ✅ Verificar que el puerto sea 8003 (no 8000)
- ✅ Verificar que el simulador esté corriendo: `docker compose ps simulator`
- ✅ Verificar logs: `docker compose logs simulator --tail 20`

---

## 📚 Referencias Técnicas

### Tablas de Base de Datos Relevantes
- `telemetry_device_parameter`: Configura qué parámetros puede enviar cada dispositivo
- `service_requests`: Solicitudes de servicio activas
- `obd_fault_machinery`: Whitelist de códigos OBD por maquinaria
- `event_type_machinery`: Configuración de tipos de evento por maquinaria
- `tolerance_thresholds`: Umbrales para generar alertas

### Mapeo de Parámetros AVL ID
| Campo | AVL ID | Descripción |
|-------|--------|-------------|
| `ignition_status` | 239 | Estado de Ignición |
| `movement_status` | 240 | Estado de Movimiento |
| `speed` | 24 | Velocidad |
| `gps_location` | 387 | Ubicación GPS |
| `gsm_signal` | 21 | Señal GSM |
| `rpm` | 36 | Revoluciones del motor |
| `engine_temp` | 32 | Temperatura del motor |
| `engine_load` | 31 | Carga del motor |
| `oil_level` | 1159 | Nivel de aceite |
| `fuel_level` | 48 | Nivel de combustible |
| `fuel_used_gps` | 12 | Combustible usado GPS |
| `instant_consumption` | 60 | Consumo instantáneo |
| `obd_faults` | 281 | Fallas OBD |
| `odometer_total` | 16 | Odómetro total |
| `odometer_trip` | 199 | Odómetro del viaje |
| `event_type` | 253 | Tipo de evento |
| `event_g_value` | 254 | Valor G del evento |

---

## 🔒 Seguridad

### Recomendaciones para Producción
1. **Usar HTTPS/WSS:** Cambiar `ws://` por `wss://` en producción
2. **Contraseña fuerte:** Usar contraseña compleja y cambiarla periódicamente
3. **Autenticación adicional:** Considerar autenticación JWT además de la contraseña
4. **Rate limiting:** Implementar límites de conexiones por IP
5. **Validación de origen:** Restringir conexiones por origen permitido

---

## 📞 Soporte

Para problemas o preguntas sobre el WebSocket de telemetría, revisar:
- Logs del simulador: `docker compose logs simulator`
- Logs del procesador: `docker compose logs telemetry_processor`
- Configuración de variables de entorno: `.env`
- Documentación de la API: `http://localhost:8003/docs`

