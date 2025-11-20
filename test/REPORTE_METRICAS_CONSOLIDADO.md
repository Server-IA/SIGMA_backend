# Reporte Consolidado de Métricas de Pruebas Unitarias

**Fecha de Generación:** 20/11/2025 16:55:55

---

## Resumen Ejecutivo

- **Total de Pruebas Unitarias Analizadas:** 66
- **Total de Pruebas Ejecutadas:** 9
- **Pruebas Exitosas:** 0
- **Pruebas Fallidas:** 0
- **Tasa de Éxito Global:** 0.00%
- **Total de Endpoints Probados:** 20
- **Pruebas con Métricas de Rendimiento:** 17

---

## 1. Tiempo de Respuesta Promedio por Microservicio

| Microservicio | Tiempo Promedio (s) | Tiempo Mínimo (s) | Tiempo Máximo (s) | Número de Mediciones |
|---------------|---------------------|-------------------|-------------------|----------------------|
| Clientes | 5.239 | 0.002 | 29.540 | 8 |
| Gestión de Datos | 4.020 | 4.020 | 4.020 | 2 |
| Mantenimiento | 2.250 | 2.250 | 2.250 | 1 |
| Maquinaria | 3.562 | 1.300 | 5.680 | 4 |
| Monitoreo | 2.150 | 2.150 | 2.150 | 2 |
| Servicios | 3.000 | 3.000 | 3.000 | 1 |
| Solicitudes | 6.981 | 0.014 | 36.080 | 11 |

---

## 2. Consumo de CPU y RAM en Pruebas

**Nota:** Las pruebas unitarias actuales no incluyen mediciones explícitas de CPU y RAM.
Para obtener estas métricas, se recomienda:

1. **Usar herramientas de profiling:** `cProfile`, `memory_profiler`, `py-spy`
2. **Monitoreo durante ejecución:** `psutil` para medir CPU y memoria
3. **Integración con CI/CD:** Agregar métricas de recursos en pipelines
4. **Pruebas de carga:** Usar herramientas como `locust`, `k6` o `JMeter`

**Ejemplo de implementación:**
```python
import psutil
import os

process = psutil.Process(os.getpid())
cpu_percent = process.cpu_percent(interval=1)
memory_info = process.memory_info()
memory_mb = memory_info.rss / 1024 / 1024
```

---

## 3. Número de Solicitudes Procesadas sin Error

| Microservicio | Pruebas Exitosas | Pruebas Fallidas | Tasa de Éxito (%) |
|---------------|------------------|------------------|-------------------|
| Maquinaria | 0 | 0 | 0.00% |

---

## 4. Tabla de Endpoints Probados y sus Tiempos

| Endpoint | Microservicio | Test ID | Tiempo Promedio (s) | Tiempo Mínimo (s) | Tiempo Máximo (s) |
|----------|---------------|---------|---------------------|-------------------|-------------------|
| `/customers` | Clientes | UT-CLI-003 | 5.770 | 5.770 | 5.770 |
| `/customers/` | Clientes | UT-CLI-002 | 0.826 | 0.002 | 3.000 |
| `/customers/create_customer/` | Clientes | UT-CLI-001 | 10.947 | 0.300 | 29.540 |
| `/established_contracts/create_established_contract/` | Contratos | UT-CON-001 | *No medido* | - | - |
| `/established_contracts/create_established_contract/` | Contratos | UT-CON-002 | *No medido* | - | - |
| `/established_contracts/create_established_contract/` | Contratos | UT-CON-003 | *No medido* | - | - |
| `/established_contracts/list/` | Contratos | UT-CON-004_Listary | *No medido* | - | - |
| `/invoices/` | Solicitudes | UT-SOL-009 | 4.070 | 4.070 | 4.070 |
| `/machinery-usage/create/` | Maquinaria | UT-MAQ-004 | *No medido* | - | - |
| `/machinery/create-general-sheet/` | Maquinaria | UT-MAQ-001 | *No medido* | - | - |
| `/maintenance/99999/` | Gestión de Mantenimiento | UT-GM-003 | *No medido* | - | - |
| `/maintenance_request` | Mantenimiento | UT-SM-005 | *No medido* | - | - |
| `/maintenance_request` | Mantenimiento | UT-SM-006 | *No medido* | - | - |
| `/maintenance_request/create/` | Mantenimiento | UT-SM-001 | 2.250 | 2.250 | 2.250 |
| `/service_requests/create_request/` | Solicitudes | UT-SOL-002 | 1.411 | 0.014 | 3.000 |
| `/service_requests/list/` | Solicitudes | UT-SOL-003 | *No medido* | - | - |
| `/services/` | Servicios | UT-SER-002 | *No medido* | - | - |
| `/services/9999/update/` | Servicios | UT-SER-003 | *No medido* | - | - |
| `/services/create/` | Servicios | UT-SER-001 | 3.000 | 3.000 | 3.000 |
| `/tolerance-thresholds/create/` | Maquinaria | UT-MAQ-021 | *No medido* | - | - |

---

## 5. Métricas de Carga (Stress Test, Concurrent Users)

**Nota:** Las pruebas unitarias actuales no incluyen pruebas de carga explícitas.
Para implementar pruebas de carga, se recomienda:

### Opciones de Implementación:

#### 1. **Locust** (Python)
```python
from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def create_customer(self):
        self.client.post('/customers/create_customer/', json={...})
```

#### 2. **k6** (JavaScript)
```javascript
import http from 'k6/http';

export let options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 50 },
  ],
};

export default function () {
  http.post('http://api/customers/create_customer/', ...);
}
```

#### 3. **JMeter** (GUI)
- Crear plan de prueba con Thread Groups
- Configurar HTTP Request Samplers
- Agregar listeners para métricas

### Métricas Recomendadas a Medir:

- **Usuarios Concurrentes:** Número máximo de usuarios simultáneos
- **Requests por Segundo (RPS):** Throughput del sistema
- **Tiempo de Respuesta bajo Carga:** P50, P95, P99
- **Tasa de Error:** Porcentaje de requests fallidos
- **CPU y Memoria:** Consumo de recursos bajo carga
- **Tiempo de Recuperación:** Después de remover la carga

---

## 6. Detalle por Prueba Unitaria

| Test ID | Microservicio | Endpoints | Pruebas Totales | Exitosas | Fallidas | Tasa Éxito | Tiempo Promedio (s) |
|---------|---------------|-----------|-----------------|----------|----------|------------|---------------------|
| UT-CLI-001 | Clientes | `/customers/create_customer/` | 0 | 0 | 0 | 0.0% | 10.947 |
| UT-CLI-002 | Clientes | `/customers/` | 0 | 0 | 0 | 0.0% | 0.826 |
| UT-CLI-003 | Clientes | `/customers` | 0 | 0 | 0 | 0.0% | 5.770 |
| UT-CLI-004 | Clientes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CLI-005 | Clientes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-001 | Contratos | `/established_contracts/create_established_contract...` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-002 | Contratos | `/established_contracts/create_established_contract...` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-003 | Contratos | `/established_contracts/create_established_contract...` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-004 | Contratos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-004_Listary | Contratos | `/established_contracts/list/` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-005 | Contratos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-006 | Contratos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-007 | Contratos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-CON-009 | Contratos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-GD-001 | Gestión de Datos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-GD-002 | Gestión de Datos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 4.020 |
| UT-GD-004 | Gestión de Datos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-GM-003 | Gestión de Mantenimiento | `/maintenance/99999/` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-GM-004 | Gestión de Mantenimiento | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-001 | Maquinaria | `/machinery/create-general-sheet/` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-003 | Maquinaria | `*Sin endpoint*` | 9 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-004 | Maquinaria | `/machinery-usage/create/` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-008 | Maquinaria | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 5.170 |
| UT-MAQ-010 | Maquinaria | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-011 | Maquinaria | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-013 | Maquinaria | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-021 | Maquinaria | `/tolerance-thresholds/create/` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-022 | Maquinaria | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MAQ-164 (009) | Maquinaria | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 5.680 |
| UT-MAQ-165 (009) | Maquinaria | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 2.100 |
| UT-MAQ-166 (009) | Maquinaria | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 1.300 |
| UT-MS-001 | Monitoreo | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MS-006 | Monitoreo | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-MS-007 | Monitoreo | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 2.150 |
| UT-MS-009 | Monitoreo | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-002 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-003 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-004 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-005 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-006 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-007 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-009 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-010 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PARA-011 | Parametrización | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PM-001 | Pagos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PM-002 | Pagos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PM-003 | Pagos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-PM-004 | Pagos | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SER-001 | Servicios | `/services/create/` | 0 | 0 | 0 | 0.0% | 3.000 |
| UT-SER-002 | Servicios | `/services/` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SER-003 | Servicios | `/services/9999/update/` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SER-004 | Servicios | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SM-001 | Mantenimiento | `/maintenance_request/create/` | 0 | 0 | 0 | 0.0% | 2.250 |
| UT-SM-003 | Mantenimiento | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SM-005 | Mantenimiento | `/maintenance_request` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SM-006 | Mantenimiento | `/maintenance_request` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SOL-001 | Solicitudes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SOL-002 | Solicitudes | `/service_requests/create_request/` | 0 | 0 | 0 | 0.0% | 1.411 |
| UT-SOL-003 | Solicitudes | `/service_requests/list/` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SOL-004 | Solicitudes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SOL-005 | Solicitudes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 8.180 |
| UT-SOL-007 | Solicitudes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 10.160 |
| UT-SOL-008 | Solicitudes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 36.080 |
| UT-SOL-009 | Solicitudes | `/invoices/` | 0 | 0 | 0 | 0.0% | 4.070 |
| UT-SOL-010 | Solicitudes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | *No medido* |
| UT-SOL-011 | Solicitudes | `*Sin endpoint*` | 0 | 0 | 0 | 0.0% | 9.830 |

---

## Recomendaciones

1. **Implementar mediciones sistemáticas de tiempo de respuesta** en todas las pruebas
2. **Agregar métricas de CPU y RAM** usando herramientas de profiling
3. **Crear suite de pruebas de carga** para endpoints críticos
4. **Establecer SLAs** para tiempos de respuesta por microservicio
5. **Monitoreo continuo** en ambiente de producción
6. **Documentar métricas** en cada ejecución de pruebas

---

*Reporte generado automáticamente el 20/11/2025 16:55:55*