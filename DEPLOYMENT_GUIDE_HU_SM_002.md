# Guía de Actualización y Despliegue - HU-SM-002

## Pasos para Aplicar los Cambios

### 1. Preparación del Entorno

Asegúrese de tener Docker y Docker Compose instalados y configurados.

```bash
# Verificar que la red compartida existe
docker network ls | grep shared_net

# Si no existe, crearla
docker network create shared_net
```

### 2. Configurar Variables de Entorno

Agregar/verificar las siguientes variables en su archivo `.env`:

```env
# Configuración existente
SECRET_KEY=your_secret_key
DB_NAME=machpaydb
DB_USER=youruser
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432
DEBUG=True
ALLOWED_HOSTS=*
AUTH_SERVICE_URL=http://backend:8001/
JWT_SECRET=your_secret_key

# Configuración del Job de Mantenimiento Automático
ACTIVE_MACHINERY_STATUS_ID=4
PENDING_REQUEST_STATUS_ID=10
MAINTENANCE_TYPE_CATEGORY_ID=12
PRIORITY_CATEGORY_ID=13
MAINTENANCE_TYPE_PREVENTIVE_ID=14
MAINTENANCE_TYPE_CORRECTIVE_ID=15
DEFAULT_PRIORITY_TYPE_ID=16
INACTIVITY_DAYS_THRESHOLD=14

# NUEVO: Para notificaciones de incidentes de sensores
MAINTENANCE_CHIEF_PERMISSION_ID=121
```

### 3. Levantar el Contenedor

```bash
# Construir y levantar los servicios
docker-compose up -d --build

# Verificar que los contenedores estén corriendo
docker ps
```

### 4. Ejecutar Migraciones

```bash
# Aplicar las nuevas migraciones
docker exec machpay_backend python manage.py migrate

# Verificar que las migraciones se aplicaron correctamente
docker exec machpay_backend python manage.py showmigrations maintenance machinery
```

**Salida esperada:**
```
maintenance
 [X] 0001_initial
 ...
 [X] 0020_remove_maintenancereport_creation_date
 [X] 0021_auto_maintenance_job_improvements

machinery
 [X] 0001_initial
 ...
 [X] 0016_merge_20251004_0033
 [X] 0017_add_next_maintenance_date
```

### 5. Verificar la Base de Datos

```bash
# Conectarse a PostgreSQL
docker exec -it machpay_db psql -U youruser -d machpaydb

# Verificar tablas nuevas/modificadas
\d maintenance_request
\d sensor_reading_incident
\d periodic_maintenance_scheduling
```

**Verificaciones esperadas:**
- `maintenance_request.detected_at` debe ser de tipo `timestamp with time zone`
- `maintenance_request.is_automatic` debe existir (boolean, default false)
- Debe existir la tabla `sensor_reading_incident`
- `periodic_maintenance_scheduling.next_maintenance_date` debe existir (date, nullable)

### 6. Probar el Job en Modo Dry-Run

```bash
# Ejecutar sin crear solicitudes (modo prueba)
docker exec machpay_backend python manage.py generate_auto_maintenance_requests --dry-run
```

**Salida esperada:**
```json
{
  "dry_run": true,
  "checked_periodic": X,
  "created_periodic": Y,
  "checked_inactivity": Z,
  "created_inactivity": W,
  "generated_at": "2025-XX-XXTXX:XX:XX..."
}
```

### 7. Crear Datos de Prueba

Para probar el job, necesita datos de prueba:

```python
# Desde el shell de Django
docker exec -it machpay_backend python manage.py shell

from machinery.models import Machinery, PeriodicMaintenanceScheduling, MachineryUsageSheet
from maintenance.models import Maintenance
from parameterization.models import Statues, Types
from django.utils import timezone
from datetime import timedelta

# Obtener maquinaria activa
machinery = Machinery.objects.filter(machinery_operational_status_id=4).first()

# Crear mantenimiento de prueba
maintenance = Maintenance.objects.create(
    name="Mantenimiento Preventivo Test",
    description="Prueba del job automático",
    maintenance_type_id=14,  # Preventivo
    maintenance_status_id=5,  # Activo
    id_responsible_user_id=1
)

# Configurar programación por fecha (vencida)
PeriodicMaintenanceScheduling.objects.create(
    machinery=machinery,
    maintenance=maintenance,
    next_maintenance_date=timezone.now().date() - timedelta(days=1)
)
```

### 8. Ejecutar el Job en Modo Real

```bash
# Ejecutar el job para crear solicitudes reales
docker exec machpay_backend python manage.py generate_auto_maintenance_requests
```

### 9. Verificar Solicitudes Creadas

```bash
# Desde el shell de Django
docker exec -it machpay_backend python manage.py shell

from maintenance.models import MaintenanceRequest

# Ver solicitudes automáticas creadas
requests = MaintenanceRequest.objects.filter(is_automatic=True)
for req in requests:
    print(f"{req.id_maintenance_request} - {req.description} - {req.detected_at}")
```

### 10. Verificar Incidentes de Sensores

```bash
# Desde el shell de Django
docker exec -it machpay_backend python manage.py shell

from maintenance.models import SensorReadingIncident

# Ver incidentes registrados
incidents = SensorReadingIncident.objects.all()
for inc in incidents:
    print(f"{inc.id_sensor_incident} - {inc.incident_type} - Notified: {inc.notified}")
```

### 11. Configurar Ejecución Automática

#### Opción A: Cron Job (Linux/Unix)

```bash
# Editar crontab
crontab -e

# Ejecutar cada hora
0 * * * * docker exec machpay_backend python manage.py generate_auto_maintenance_requests

# O ejecutar cada 4 horas
0 */4 * * * docker exec machpay_backend python manage.py generate_auto_maintenance_requests
```

#### Opción B: Celery (Recomendado para producción)

Agregar tarea periódica en `celery.py`:

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('machpaymanager')

app.conf.beat_schedule = {
    'generate-auto-maintenance-requests': {
        'task': 'maintenance.tasks.generate_auto_requests',
        'schedule': crontab(hour='*/4'),  # Cada 4 horas
    },
}
```

#### Opción C: Django-Q o Django-Cron

Configurar según la documentación de la librería elegida.

### 12. Monitoreo y Logs

```bash
# Ver logs del backend
docker logs -f machpay_backend

# Buscar eventos del job
docker logs machpay_backend 2>&1 | grep "Resultado job solicitudes automáticas"

# Ver errores de sensores
docker logs machpay_backend 2>&1 | grep "Incidente de sensor"
```

### 13. Validación en Interfaz de Usuario

1. **Listar Solicitudes**: Verificar que aparezcan las solicitudes automáticas con el badge o indicador correspondiente
2. **Detalle de Solicitud**: Ver que muestra fecha y hora completa de detección
3. **Intentar Rechazar Automática**: Debe mostrar error indicando que no se puede rechazar
4. **Admin Django**: 
   - Acceder a `/admin/maintenance/maintenancerequest/`
   - Verificar que no se puedan editar/eliminar solicitudes automáticas
   - Acceder a `/admin/maintenance/sensorreadingincident/`
   - Ver los incidentes registrados

## Rollback (en caso de problemas)

Si necesita revertir los cambios:

```bash
# Revertir migraciones de maintenance
docker exec machpay_backend python manage.py migrate maintenance 0020_remove_maintenancereport_creation_date

# Revertir migraciones de machinery
docker exec machpay_backend python manage.py migrate machinery 0016_merge_20251004_0033

# Reconstruir con la versión anterior del código
git checkout <commit-anterior>
docker-compose up -d --build
```

## Solución de Problemas Comunes

### Error: "relation does not exist"
```bash
# Asegurarse de que las migraciones se ejecutaron
docker exec machpay_backend python manage.py migrate --run-syncdb
```

### Error: "constraint pm_exactly_one_trigger does not exist"
```bash
# Eliminar manualmente la restricción antigua si existe
docker exec -it machpay_db psql -U youruser -d machpaydb
ALTER TABLE periodic_maintenance_scheduling DROP CONSTRAINT IF EXISTS pm_exactly_one_trigger;
\q

# Re-ejecutar migraciones
docker exec machpay_backend python manage.py migrate machinery 0017_add_next_maintenance_date
```

### Job no crea solicitudes
```bash
# Verificar que existe maquinaria activa
docker exec machpay_backend python manage.py shell -c "from machinery.models import Machinery; print(Machinery.objects.filter(machinery_operational_status_id=4).count())"

# Verificar configuraciones periódicas
docker exec machpay_backend python manage.py shell -c "from machinery.models import PeriodicMaintenanceScheduling; print(PeriodicMaintenanceScheduling.objects.count())"

# Revisar logs en detalle
docker exec machpay_backend python manage.py generate_auto_maintenance_requests --dry-run
```

## Contacto y Soporte

Para dudas o problemas, contactar al equipo de desarrollo o revisar:
- Documento de implementación: `IMPLEMENTATION_HU_SM_002.md`
- Logs del sistema: `docker logs machpay_backend`
- Base de datos: tabla `sensor_reading_incident` para errores registrados
