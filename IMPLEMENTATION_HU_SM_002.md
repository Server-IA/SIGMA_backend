# Implementación de HU-SM-002: Generación Automática de Solicitudes de Mantenimiento

## Resumen de Cambios

Este documento describe los cambios implementados para cumplir con todos los criterios de aceptación de la Historia de Usuario HU-SM-002.

## Criterios de Aceptación Implementados

### 1. ✅ Generación automática según criterios

El sistema genera automáticamente solicitudes de mantenimiento cuando:
- **Horas de uso**: Se alcanza el umbral de horas configurado
- **Distancia**: Se alcanza la distancia configurada (km)
- **Fecha programada**: Se alcanza o supera la fecha de mantenimiento preventivo programado (**NUEVO**)
- **Inactividad prolongada**: La maquinaria ha estado inactiva por más de X días (configurable)

### 2. ✅ Datos obligatorios en la solicitud

Cada solicitud automática incluye:
- **Identificador único**: Formato SOL-YYYY-NNNN (consecutivo por año) (**NUEVO**)
- **Maquinaria**: ID de la maquinaria que requiere mantenimiento
- **Tipo de mantenimiento**: Preventivo, correctivo, etc.
- **Prioridad**: Configurada según el tipo de evento
- **Descripción**: Detalle del motivo que disparó la solicitud
- **Fecha y hora de detección**: Timestamp completo (DateTime) (**ACTUALIZADO**)
- **Marca de automática**: Campo `is_automatic=True` (**NUEVO**)

### 3. ✅ Registro en estado "Pendiente"

Las solicitudes se crean con estado ID=10 (Pendiente) y quedan registradas en la base de datos.

### 4. ✅ Notificaciones

Se envía notificación al servicio de autenticación para usuarios con permisos de autorización.

### 5. ✅ Filtro por estado de maquinaria

El sistema NO genera solicitudes para maquinaria inactiva o fuera de servicio (solo para estado ID=4 - Activo).

### 6. ✅ Historial sin modificación/eliminación

- Campo `is_automatic` marca las solicitudes generadas automáticamente
- El endpoint `reject` valida que no se puedan rechazar solicitudes automáticas
- No existen endpoints de actualización o eliminación para MaintenanceRequest

### 7. ✅ Registro de incidentes de sensores

- Nuevo modelo `SensorReadingIncident` para registrar errores
- El job registra y notifica errores de lectura de:
  - Datos de sensores inválidos
  - Conversiones de unidades fallidas
  - Evaluación de fechas con errores
  - Hojas de uso faltantes

## Archivos Modificados

### Modelos

1. **maintenance/models/sensor_reading_incident.py** (NUEVO)
   - Modelo para registrar incidentes de sensores/telemetría
   - Incluye notificación al jefe de mantenimiento

2. **maintenance/models/maintenance_request.py**
   - Campo `detected_at` cambiado de `DateField` a `DateTimeField`
   - Nuevo campo `is_automatic` para marcar solicitudes automáticas

3. **machinery/models/periodic_maintenance.py**
   - Nuevo campo `next_maintenance_date` para mantenimiento preventivo basado en fecha
   - Actualizada restricción para permitir múltiples criterios de disparo

### Lógica del Job

4. **maintenance/services/auto_maintenance_job.py**
   - `_generate_request_id()`: Genera consecutivo SOL-YYYY-NNNN
   - `_log_sensor_incident()`: Registra y notifica incidentes
   - `_create_request()`: Actualizado para usar DateTime y generar ID
   - `_evaluate_periodic_schedules()`: 
     - Evalúa fecha programada (NUEVO)
     - Manejo robusto de errores con logging de incidentes
     - Usa DateTime para detected_at

### API y Serializers

5. **maintenance/api/maintenance_request_viewset.py**
   - Validación en `reject_request` para bloquear rechazo de solicitudes automáticas

6. **maintenance/serializers/.../maintenance_request_create_serializer.py**
   - Actualizado `validate_detected_at` para aceptar DateTime

7. **maintenance/serializers/.../maintenance_request_list_serializer.py**
   - Campo `fecha_solicitud` actualizado a `DateTimeField`
   - Nuevo campo `is_automatic` en la lista

### Migraciones

8. **maintenance/migrations/0021_auto_maintenance_job_improvements.py**
   - Altera campo `detected_at` a DateTime
   - Agrega campo `is_automatic`
   - Crea modelo `SensorReadingIncident`

9. **machinery/migrations/0017_add_next_maintenance_date.py**
   - Agrega campo `next_maintenance_date`
   - Actualiza restricción de triggers

## Variables de Entorno

El job puede configurarse mediante variables de entorno:

```bash
# Estados y tipos
ACTIVE_MACHINERY_STATUS_ID=4
PENDING_REQUEST_STATUS_ID=10
MAINTENANCE_TYPE_CATEGORY_ID=12
PRIORITY_CATEGORY_ID=13
MAINTENANCE_TYPE_PREVENTIVE_ID=14
MAINTENANCE_TYPE_CORRECTIVE_ID=15
DEFAULT_PRIORITY_TYPE_ID=16

# Umbrales
INACTIVITY_DAYS_THRESHOLD=14

# Notificaciones
MAINTENANCE_CHIEF_PERMISSION_ID=121  # Nuevo: ID del permiso del jefe de mantenimiento
AUTH_SERVICE_URL=http://backend:8001/
```

## Ejecución del Job

```bash
# Dry run (sin crear solicitudes)
docker exec machpay_backend python manage.py generate_auto_maintenance_requests --dry-run

# Ejecución real
docker exec machpay_backend python manage.py generate_auto_maintenance_requests
```

## Flujo de Datos

### 1. Mantenimiento Preventivo por Fecha

```
PeriodicMaintenanceScheduling.next_maintenance_date
  ↓ (si fecha <= hoy)
Crear MaintenanceRequest
  - tipo: preventivo
  - prioridad: según configuración
  - descripción: "Fecha de mantenimiento programada alcanzada o vencida (YYYY-MM-DD)"
```

### 2. Registro de Incidentes

```
Error al leer sensor/telemetría
  ↓
Crear SensorReadingIncident
  ↓
Enviar notificación a jefe de mantenimiento (permission_id=121)
  ↓
Marcar incidente como notificado
```

## Criterios de Aceptación - Checklist Completo

- [x] ✅ 1. Generación automática por horas de uso
- [x] ✅ 2. Generación automática por fecha programada (IMPLEMENTADO)
- [x] ✅ 3. Generación automática por inactividad
- [x] ✅ 4. Datos obligatorios con consecutivo y timestamp completo
- [x] ✅ 5. Registro en estado "Pendiente"
- [x] ✅ 6. Notificación a autorizadores
- [x] ✅ 7. No generar para maquinaria inactiva
- [x] ✅ 8. Protección contra modificación/eliminación
- [x] ✅ 9. Registro y notificación de errores de sensores

## Próximos Pasos

1. Ejecutar migraciones en entorno de desarrollo/test
2. Validar la generación de solicitudes con datos de prueba
3. Verificar notificaciones a usuarios con permisos
4. Configurar cron job o scheduled task para ejecución periódica del comando
5. Documentar en manual de usuario el funcionamiento de solicitudes automáticas

## Notas Técnicas

- Las solicitudes automáticas NO pueden ser rechazadas, solo pueden ser programadas o quedar en estado pendiente
- El campo `is_automatic` permite distinguir solicitudes manuales de automáticas en la interfaz
- Los incidentes de sensores se almacenan permanentemente para auditoría
- El job es idempotente: no crea solicitudes duplicadas si ya existe una pendiente del mismo tipo
