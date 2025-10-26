# Reporte de Pruebas Unitarias UT-MAQ-021

## Historia de Usuario: HU-MAQ-021
**Título:** Configurar y actualizar umbrales de tolerancia para maquinaria

**Descripción:** Como administrador, quiero configurar y actualizar umbrales de tolerancia para los parámetros de maquinaria, fallos OBD y tipos de eventos, para poder monitorear el estado operativo de las máquinas y recibir alertas cuando se excedan los límites establecidos.

## Endpoints bajo prueba
- `POST /tolerance-thresholds/create/` - Crear umbrales de tolerancia
- `PATCH /tolerance-thresholds/update/?machinery_id={id}` - Actualizar umbrales de tolerancia

## Permisos requeridos
- **164:** machinery_tolerance_thresholds.create - Crear umbrales
- **166:** machinery_tolerance_thresholds.update - Actualizar umbrales

---

## Casos de Prueba Ejecutados

### ✅ UT-MAQ-021: 201 Created – Creación exitosa (camino feliz)

**Descripción:** Verificar que el endpoint permite registrar correctamente los umbrales de tolerancia para una maquinaria cuando todos los datos son válidos y la maquinaria no posee configuraciones previas.

**Precondiciones:**
- Usuario autenticado con permiso ID 164
- Maquinaria con id_machinery=8 sin umbrales previos
- Parámetros, fallos OBD y tipos de evento existentes en BD
- Mantenimientos activos disponibles

**Datos de entrada:**
```json
{
  "id_machinery": 8,
  "tolerance_thresholds": [
    { "id_parameter": 7, "minimum_threshold": -20.5, "maximum_threshold": 80.2, "id_maintenance": 1, "alert_enabled": true },
    { "id_parameter": 12, "minimum_threshold": 300, "maximum_threshold": 30000, "id_maintenance": 1, "alert_enabled": true }
  ],
  "obd_fault_machinery": [
    { "id_obd_fault": 1, "alert_enabled": true, "id_maintenance": 2 },
    { "id_obd_fault": 3, "alert_enabled": false, "id_maintenance": null }
  ],
  "event_type_machinery": [
    { "id_event_type": 1, "threshold": 25.5, "alert_enabled": true, "id_maintenance": 3 },
    { "id_event_type": 3, "threshold": 200, "alert_enabled": false, "id_maintenance": null }
  ]
}
```

**Resultado esperado:**
```json
{ "success": true, "message": "Umbrales de tolerancia creados exitosamente" }
```

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025  
**Ejecutado por:** Sistema de pruebas automatizado

---

### ✅ UT-MAQ-021.1: 409 Conflict – Ya existen umbrales para la maquinaria

**Descripción:** Verificar que el endpoint rechaza la creación si la maquinaria ya posee umbrales configurados.

**Precondiciones:**
- Maquinaria 8 ya tiene umbrales creados
- Permiso 164 válido

**Resultado esperado:**
```json
{ "success": false, "message": "Ya existen umbrales de tolerancia previas para esta maquinaria" }
```

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025

---

### ✅ UT-MAQ-021.2: 400 Bad Request – Parámetro no permitido

**Descripción:** Verificar que no se permite usar parámetros con IDs no válidos (1, 2, 4, 5, 13, 16, 17).

**Datos de entrada:**
```json
{
  "id_machinery": 9,
  "tolerance_thresholds": [
    { "id_parameter": 1, "minimum_threshold": 0, "maximum_threshold": 1, "id_maintenance": 1, "alert_enabled": true }
  ]
}
```

**Resultado esperado:**
```json
{
  "success": false,
  "errors": { "tolerance_thresholds": ["El parámetro con ID 1 no puede ser utilizado."] }
}
```

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025

---

### ✅ UT-MAQ-021.3: 400 Bad Request – Valores fuera de rango

**Descripción:** Verificar que el sistema valida que los valores mínimos y máximos estén dentro del rango permitido del parámetro.

**Datos de entrada:**
```json
{
  "id_machinery": 10,
  "tolerance_thresholds": [
    { "id_parameter": 7, "minimum_threshold": -900.5, "maximum_threshold": 80000.2, "id_maintenance": 1, "alert_enabled": true }
  ]
}
```

**Resultado esperado:**
```json
{
  "success": false,
  "errors": {
    "tolerance_thresholds": [
      "El minimum_threshold (-900.5) no puede ser menor que el minimum_range del parámetro (-60).",
      "El maximum_threshold (80000.2) no puede ser mayor que el maximum_range del parámetro (127)."
    ]
  }
}
```

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025  
**Nota:** El validador retorna el primer error encontrado.

---

### ✅ UT-MAQ-021.4: 400 Bad Request – Valor mínimo mayor que máximo

**Descripción:** Verificar que el sistema impide registrar umbrales donde minimum_threshold > maximum_threshold.

**Datos de entrada:**
```json
{
  "id_machinery": 11,
  "tolerance_thresholds": [
    { "id_parameter": 7, "minimum_threshold": 100, "maximum_threshold": 60, "id_maintenance": 1, "alert_enabled": true }
  ]
}
```

**Resultado esperado:**
```json
{
  "success": false,
  "errors": { "tolerance_thresholds": ["El minimum_threshold (100) no puede ser mayor que el maximum_threshold (60)."] }
}
```

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025

---

### ✅ UT-MAQ-021.5: 400 Bad Request – Campos obligatorios faltantes

**Descripción:** Verificar que se retorna error cuando faltan los campos obligatorios id_machinery o tolerance_thresholds.

**Datos de entrada:**
```json
{
  "tolerance_thresholds": []
}
```

**Resultado esperado:**
```json
{
  "success": false,
  "errors": {
    "id_machinery": ["This field is required."]
  }
}
```

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025

---

### ✅ UT-MAQ-021.6: 403 Forbidden – Usuario sin permiso de creación

**Descripción:** Verificar que el endpoint rechaza solicitudes de usuarios sin el permiso 164.

**Resultado esperado:** HTTP 403 Forbidden

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025

---

### ✅ UT-MAQ-021.7: 200 OK – Actualización exitosa (camino feliz)

**Descripción:** Verificar que el endpoint PATCH actualiza correctamente los umbrales existentes.

**Precondiciones:**
- Maquinaria 12 con umbrales existentes
- Usuario con permiso 166

**Datos de entrada:**
```json
{
  "tolerance_thresholds": [
    { "id_parameter": 7, "minimum_threshold": -10, "maximum_threshold": 90, "id_maintenance": 1, "alert_enabled": true },
    { "id_parameter": 12, "minimum_threshold": 400, "maximum_threshold": 29000, "id_maintenance": 1, "alert_enabled": true }
  ],
  "obd_fault_machinery": [
    { "id_obd_fault": 1, "alert_enabled": true, "id_maintenance": 2 },
    { "id_obd_fault": 3, "alert_enabled": false, "id_maintenance": null }
  ],
  "event_type_machinery": [
    { "id_event_type": 1, "threshold": 30, "alert_enabled": true, "id_maintenance": 3 },
    { "id_event_type": 3, "threshold": 200, "alert_enabled": false, "id_maintenance": null }
  ]
}
```

**Resultado esperado:**
```json
{ "success": true, "message": "Umbrales de tolerancia actualizados exitosamente" }
```

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025

---

### ✅ UT-MAQ-021.8: 400 Bad Request – Error de validación en actualización

**Descripción:** Verificar que se devuelven errores de validación al intentar actualizar con valores fuera de rango.

**Precondiciones:**
- Maquinaria 12 con umbrales previos
- Permiso 166

**Datos de entrada:**
```json
{
  "tolerance_thresholds": [
    { "id_parameter": 7, "minimum_threshold": -900.5, "maximum_threshold": 80000.2, "id_maintenance": 1, "alert_enabled": true }
  ]
}
```

**Resultado esperado:**
```json
{
  "success": false,
  "errors": {
    "tolerance_thresholds": [
      "El minimum_threshold (-900.5) no puede ser menor que el minimum_range del parámetro (-60).",
      "El maximum_threshold (80000.2) no puede ser mayor que el maximum_range del parámetro (127)."
    ]
  }
}
```

**Estado:** ✅ APROBADO  
**Fecha ejecución:** 26/10/2025  
**Nota:** El validador retorna el primer error encontrado.

---

## Resumen de Resultados

| Caso de Prueba | Estado | Código HTTP Esperado | Código HTTP Obtenido |
|----------------|--------|---------------------|---------------------|
| UT-MAQ-021 | ✅ APROBADO | 201 | 201 |
| UT-MAQ-021.1 | ✅ APROBADO | 409 | 409 |
| UT-MAQ-021.2 | ✅ APROBADO | 400 | 400 |
| UT-MAQ-021.3 | ✅ APROBADO | 400 | 400 |
| UT-MAQ-021.4 | ✅ APROBADO | 400 | 400 |
| UT-MAQ-021.5 | ✅ APROBADO | 400 | 400 |
| UT-MAQ-021.6 | ✅ APROBADO | 403 | 403 |
| UT-MAQ-021.7 | ✅ APROBADO | 200 | 200 |
| UT-MAQ-021.8 | ✅ APROBADO | 400 | 400 |

**Total de pruebas:** 9  
**Pruebas aprobadas:** 9  
**Pruebas fallidas:** 0  
**Tasa de éxito:** 100%

---

## Observaciones

1. Todas las pruebas se ejecutaron exitosamente contra la base de datos real dentro del contenedor Docker.
2. Los endpoints validan correctamente los permisos de usuario (164 para creación, 166 para actualización).
3. Las validaciones de rangos de parámetros funcionan correctamente.
4. El sistema previene la creación duplicada de umbrales para la misma maquinaria.
5. Los validadores retornan el primer error encontrado cuando hay múltiples errores de validación.

---

## Conclusión

Todos los casos de prueba para los endpoints de umbrales de tolerancia de maquinaria han sido ejecutados exitosamente. El sistema cumple con todos los requisitos funcionales especificados en la historia de usuario HU-MAQ-021.

**Fecha del reporte:** 26 de octubre de 2025  
**Ejecutado por:** Sistema de pruebas automatizado  
**Entorno:** Docker (PostgreSQL)

