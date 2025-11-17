# Reporte de Pruebas Unitarias - UT-MS-007

## Resumen Ejecutivo
- **Total de Pruebas**: 6
- **Pruebas Exitosas**: 6 ✅
- **Pruebas Fallidas**: 0 ❌
- **Tasa de Éxito**: 100.0%
- **Fecha de Ejecución**: 11/10/2025
- **Ejecutado por**: Sistema de Pruebas Automatizadas

---

### Pruebas agrupadas por resultado

#### Pruebas Exitosas
- UT-MS-007
- UT-MS-007.1
- UT-MS-007.2
- UT-MS-007.3
- UT-MS-007.5
- UT-MS-007.6

#### Pruebas Fallidas
- Ninguna

---

## UT-MS-007

**Título**: 201/200 Created – Generación de maintenance requests desde service request (camino feliz)

**Payload**:
```json
{}
```

**Resultado Esperado**: HTTP 200 / 201 (creación válida de MaintenanceRequest)

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 201/200

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-MS-007.1

**Título**: 400/200 – No generar MR para maquinaria inactiva

**Payload**:
```json
{}
```

**Resultado Esperado**: No crear MaintenanceRequest para maquinaria marcada como inactiva (HTTP 200 o 201 si al menos una MR válida para otras máquinas)

**Resultado Obtenido**: ✅ **PASÓ** - Se respetó el estado inactivo y no se generaron MRs para la máquina inactiva

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-MS-007.2

**Título**: Idempotencia – Evitar duplicados al invocar el endpoint dos veces

**Payload**:
```json
{}
```

**Resultado Esperado**: Segunda invocación no debe crear duplicados; respuesta aceptable HTTP 200/201 pero sin duplicados en BD

**Resultado Obtenido**: ✅ **PASÓ** - No se generaron registros duplicados en la segunda invocación

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-MS-007.3

**Título**: Notificación/Auditoría – Se invoca cliente de auditoría/notifications (mocked)

**Payload**:
```json
{}
```

**Resultado Esperado**: El cliente de auditoría/notification es llamado (parcheado en tests)

**Resultado Obtenido**: ✅ **PASÓ** - Cliente de auditoría fue invocado según el mock

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-MS-007.5

**Título**: Manejo de datos de sensores corruptos – No producir 500

**Payload**:
```json
{}
```

**Resultado Esperado**: El endpoint maneja datos faltantes/corruptos sin lanzar error 500; respuesta válida (200/201)

**Resultado Obtenido**: ✅ **PASÓ** - No se produjo error 500; proceso completado correctamente

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

## UT-MS-007.6

**Título**: Seguridad – Acceso restringido (usuario no autenticado)

**Payload**:
```json
{}
```

**Resultado Esperado**: HTTP 401 cuando se invoca sin credenciales

**Resultado Obtenido**: ✅ **PASÓ** - HTTP 401

**Estado**: ✅ **EXITOSA**

**Fecha Ejecución**: 11/10/2025

**Ejecutado por**: Sistema de Pruebas Automatizadas

---

### Notas

- Esta ejecución se realizó dentro del contenedor de tests del proyecto (entorno Docker). La suite coleccionó 6 pruebas (coincidente con el contenido actual del archivo de tests en `test/UT-MS-007`).
- Advertencias: durante la ejecución se registraron 3 warnings menores (relacionados con dependencias y deprecaciones) que no afectaron el resultado de las pruebas.
- Si quieres que separe la HU-004 (si corresponde) en un test independiente en el archivo de tests, lo puedo hacer en la siguiente iteración.

---

**Resumen final**: Todas las pruebas de `UT-MS-007` pasaron en la ejecución actual: 6 passed, 0 failed. ✅
# Reporte de Pruebas Unitarias: HU-MS-007

**Endpoint probado:** `POST /maintenance_request/<service_request_id>/from-service-request/`

**Ubicación de pruebas:** `test/UT-MS-007/test_UT_MS_007_HU_MS-007.py`

**Framework:** pytest + Django + mocks

**Base de datos:** Real (docker)


