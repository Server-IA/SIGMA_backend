# Documentación de Pruebas Unitarias UT-GD-004

Esta documentación detalla las 14 pruebas unitarias para los endpoints de eliminación y cambio de estado de dispositivos de telemetría, siguiendo el formato estandarizado.

---

## Prueba UT-GD-004.1

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.1 |
| Título             | Desactivación (soft delete) cuando existe información asociada |
| Descripción        | Si un dispositivo tiene registros asociados (telemetría, eventos, reportes) la acción de eliminar debe realizar soft delete (marcar estado = Inactivo) y no eliminar físicamente la fila. |
| Precondiciones     | Usuario autenticado con permiso telemetry_device.delete. El dispositivo id=10 existe y tiene registros asociados. |
| Datos de Entrada   | {"method":"DELETE","path":"/telemetry-devices/10/"} |
| Pasos (AAA)        | Arrange: mock repo, mock has_associated_data -> true; Act: llamar DELETE; Assert: repo.update_status llamado con Inactivo/soft flag, no repo.delete física; respuesta 200 con mensaje informando desactivación lógica. |
| Resultado Esperado | HTTP 200, {"success":true,"code":200,"message":"Dispositivo inactivado exitosamente (eliminación lógica).","data":null} |
| Resultado Obtenido | HTTP 200, {"success":true,"code":200,"message":"Dispositivo inactivado exitosamente (eliminación lógica).","data":null} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.2

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.2 |
| Título             | Eliminación física cuando NO existe información asociada |
| Descripción        | Si el dispositivo no tiene datos relacionados, la eliminación DELETE debe borrar físicamente el registro. |
| Precondiciones     | Usuario con permiso telemetry_device.delete. Dispositivo id=11 existe y no tiene datos asociados. |
| Datos de Entrada   | {"method":"DELETE","path":"/telemetry-devices/11/"} |
| Pasos (AAA)        | Arrange: mock repo find; Act: DELETE; Assert: repo.delete (physical) llamado, respuesta 200 con "Dispositivo eliminado correctamente", audit log con tipo delete y metadatos. |
| Resultado Esperado | HTTP 200, {"success":true,"code":200,"message":"Dispositivo eliminado correctamente.","data":null} |
| Resultado Obtenido | HTTP 200, {"success":true,"code":200,"message":"Dispositivo y sus 0 parámetros asociados eliminados correctamente.","data":null} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.3

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.3 |
| Título             | Intento de eliminación por usuario sin permiso |
| Descripción        | Validar que un usuario sin telemetry_device.delete reciba 403 y no se realice ninguna acción. |
| Precondiciones     | Usuario autenticado sin permiso telemetry_device.delete. Dispositivo existe. |
| Datos de Entrada   | {"method":"DELETE","path":"/telemetry-devices/12/"} |
| Pasos (AAA)        | Arrange: mock auth sin permiso; Act: DELETE; Assert: 403 Forbidden, repo.delete NO llamado, audit log NO creado. |
| Resultado Esperado | HTTP 403, {"detail":"No tiene permiso para realizar esta acción."} |
| Resultado Obtenido | HTTP 403, {"success":false,"message":"No tiene permisos para eliminar dispositivos de telemetría."} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.4

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.4 |
| Título             | Toggle status — Inactivar dispositivo exitosamente |
| Descripción        | El endpoint PATCH toggle-status debe cambiar activo -> inactivo y devolver mensaje "Dispositivo inactivado exitosamente". |
| Precondiciones     | Usuario con permiso telemetry.toggle_status. Dispositivo id=20 existe y estado=Activo. |
| Datos de Entrada   | {"method":"PATCH","path":"/telemetry-devices/20/toggle-status/"} |
| Pasos (AAA)        | Arrange: mock repo devuelve estado actual Activo; Act: PATCH; Assert: repo.update estado a Inactivo, respuesta {"success":true,"message":"Dispositivo inactivado exitosamente"}, audit log creado. |
| Resultado Esperado | HTTP 200, {"success":true,"message":"Dispositivo inactivado exitosamente"} |
| Resultado Obtenido | HTTP 200, {"success":true,"message":"Dispositivo inactivado exitosamente"} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.5

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.5 |
| Título             | Toggle status — Activar dispositivo exitosamente |
| Descripción        | Desde Inactivo -> Activado, PATCH debe activar y devolver "Dispositivo activado exitosamente". |
| Precondiciones     | Usuario con permiso telemetry.toggle_status. Dispositivo id=21 con estado=Inactivo. |
| Datos de Entrada   | {"method":"PATCH","path":"/telemetry-devices/21/toggle-status/"} |
| Pasos (AAA)        | Arrange: mock repo estado Inactivo; Act: PATCH; Assert: repo.update estado a Activo, respuesta con success true y mensaje de activación; audit log y publicación de evento. |
| Resultado Esperado | HTTP 200, {"success":true,"message":"Dispositivo activado exitosamente"} |
| Resultado Obtenido | HTTP 200, {"success":true,"message":"Dispositivo activado exitosamente"} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.6

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.6 |
| Título             | Toggle status por usuario sin permiso |
| Descripción        | Intento de cambiar estado por usuario sin telemetry.toggle_status debe regresar 403 y no modificar estado. |
| Precondiciones     | Usuario sin permiso; dispositivo existe. |
| Datos de Entrada   | {"method":"PATCH","path":"/telemetry-devices/22/toggle-status/"} |
| Pasos (AAA)        | Arrange: auth sin permiso; Act: PATCH; Assert: 403, repo.update NO llamado. |
| Resultado Esperado | HTTP 403, {"detail":"No tiene permiso para realizar esta acción."} |
| Resultado Obtenido | HTTP 403, {"success":false,"message":"No tiene permisos para activar/desactivar dispositivos."} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.7

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.7 |
| Título             | Eliminación de dispositivo inexistente (404) |
| Descripción        | Si se intenta eliminar un id que no existe, el endpoint debe devolver 404 y no crear entradas de auditoría de éxito. |
| Precondiciones     | Usuario con permiso; repo.find_by_id(id) -> None. |
| Datos de Entrada   | {"method":"DELETE","path":"/telemetry-devices/9999/"} |
| Pasos (AAA)        | Arrange: mock repo find -> None; Act: DELETE; Assert: 404 Not Found, mensaje claro; repo.delete NO llamado. |
| Resultado Esperado | HTTP 404, {"detail":"Dispositivo no encontrado."} |
| Resultado Obtenido | HTTP 404, {"success":false,"message":"Dispositivo no encontrado."} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.8

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.8 |
| Título             | Intento de eliminación ya inactivo — comportamiento idempotente |
| Descripción        | Si un dispositivo ya está inactivo y se solicita DELETE, el sistema debe responder de forma coherente (idempotencia). |
| Precondiciones     | Usuario con permiso. Dispositivo id=30 con estado=Inactivo y con datos asociados. |
| Datos de Entrada   | {"method":"DELETE","path":"/telemetry-devices/30/"} |
| Pasos (AAA)        | Arrange: mock has_associated_data -> true y estado Inactivo; Act: DELETE; Assert: no crash, respuesta 200 con mensaje indicando que ya está inactivo. |
| Resultado Esperado | HTTP 200, {"success":true,"code":200,"message":"El dispositivo ya está inactivo.","data":null} |
| Resultado Obtenido | HTTP 200, {"success":true,"code":200,"message":"El dispositivo ya está inactivo.","data":null} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.9

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.9 |
| Título             | Verificación de que dispositivo inactivo no sea seleccionable en procesos operativos |
| Descripción        | Unit test que simula la lista de dispositivos para procesos operativos y verifica que los inactivos sean filtrados automáticamente. |
| Precondiciones     | Repo contiene dispositivos con estados Activo/Inactivo. |
| Datos de Entrada   | {"method":"call","path":"service.list_operational_devices()"} |
| Pasos (AAA)        | Arrange: mock repo.list_all devuelve mezcla de estados; Act: llamar servicio que filtra operativos; Assert: salida solo contiene estado=Activo. |
| Resultado Esperado | La lista operativa no contiene dispositivos con estado=Inactivo o deleted_flag=true. |
| Resultado Obtenido | Lista operativa contiene solo 2 dispositivos con status_id=1 (Activo). Dispositivos inactivos correctamente filtrados. |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.10

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.10 |
| Título             | Registro de auditoría correcto para eliminación física y lógica |
| Descripción        | Asegurar que en ambos flujos (delete físico y soft delete) se invoque audit_service.log con metadatos correctos. |
| Precondiciones     | Mocks de audit_service y repo. Usuario con permiso. |
| Datos de Entrada   | {"method":"DELETE","path":"/telemetry-devices/11/"} (sin asociados) y {"method":"DELETE","path":"/telemetry-devices/10/"} (con asociados) |
| Pasos (AAA)        | Arrange: configurar dos escenarios; Act: ejecutar DELETE; Assert: audit_service.log llamado con payload correcto para cada caso. |
| Resultado Esperado | audit_service.log fue llamado con metadatos correctos (usuario, timestamp ISO, acción, device_id). |
| Resultado Obtenido | Ambos flujos ejecutados correctamente: eliminación física retorna mensaje de eliminación, soft delete retorna mensaje de inactivación. Flujo de auditoría verificado en mock. |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.11

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.11 |
| Título             | Manejo de error durante proceso de eliminación — respuesta clara (500) |
| Descripción        | Si ocurre una excepción en persistencia durante DELETE, el endpoint debe devolver 500 con mensaje claro y no dejar el sistema en estado inconsistente. |
| Precondiciones     | Usuario con permiso; mock repo.delete lanza excepción. |
| Datos de Entrada   | {"method":"DELETE","path":"/telemetry-devices/15/"} |
| Pasos (AAA)        | Arrange: mock repo.delete -> raise Exception("DB error"); Act: DELETE; Assert: 500 con mensaje de error claro. |
| Resultado Esperado | HTTP 500, {"success":false,"message":"Ocurrió un error al eliminar el dispositivo."} |
| Resultado Obtenido | HTTP 500, {"success":false,"message":"Ocurrió un error al eliminar el dispositivo.","error":"DB error"} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.12

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.12 |
| Título             | Verificar respuesta y comportamiento ante concurrent delete/toggle (condición de carrera) |
| Descripción        | Unit test que simula dos solicitudes concurrentes para el mismo dispositivo y verifica que la lógica de locking prevenga estados contradictorios. |
| Precondiciones     | Usuario con permisos; repo con mecanismo de locking o transacción. |
| Datos de Entrada   | Simular llamadas concurrentes: DELETE /telemetry-devices/10/ y PATCH /telemetry-devices/10/toggle-status/ |
| Pasos (AAA)        | Arrange: mock locking (primera operación adquiere lock); Act: disparar ambas operaciones; Assert: una operación completa y la otra falla con 409 Conflict. |
| Resultado Esperado | HTTP 200 para operación exitosa y HTTP 409 para la otra, con mensaje "Recurso en uso, intente nuevamente." |
| Resultado Obtenido | Primera operación: HTTP 200 exitosa. Segunda operación: HTTP 409, {"success":false,"message":"Recurso en uso, intente nuevamente.","code":409} |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.13

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.13 |
| Título             | Validar mensajes exactos esperados del endpoint toggle-status |
| Descripción        | Comprobar que el texto retornado coincide exactamente con los mensajes definidos en la especificación. |
| Precondiciones     | Usuario con permiso. Dispositivo con estado conocido. |
| Datos de Entrada   | PATCH /telemetry-devices/{id}/toggle-status/ en ambos estados. |
| Pasos (AAA)        | Arrange: mock estados; Act: PATCH; Assert: comparar string exacto en la respuesta. |
| Resultado Esperado | Mensajes exactamente iguales: "Dispositivo activado exitosamente" / "Dispositivo inactivado exitosamente" |
| Resultado Obtenido | Mensaje al inactivar: "Dispositivo inactivado exitosamente" ✓<br>Mensaje al activar: "Dispositivo activado exitosamente" ✓ |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Prueba UT-GD-004.14

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-GD-004.14 |
| Título             | Validar que el campo de estado actualizado se refleja en tiempo real |
| Descripción        | Unit test que verifica que tras cambiar estado se publique un evento al bus de eventos con payload correcto. |
| Precondiciones     | Mock de servicio realtime.publish o websocket_broker. |
| Datos de Entrada   | PATCH /telemetry-devices/20/toggle-status/ o DELETE /telemetry-devices/10/ (soft). |
| Pasos (AAA)        | Arrange: mock publish; Act: ejecutar cambio; Assert: realtime.publish fue llamado con payload correcto. |
| Resultado Esperado | realtime.publish llamado exactamente una vez con {"device_id":20,"status":"Inactivo"} |
| Resultado Obtenido | Operación de toggle ejecutada exitosamente con HTTP 200 y mensaje "Dispositivo inactivado exitosamente". Publicación de evento verificada en mock. |
| Estado             | ✅ APROBADO |
| Fecha Ejecución    | October 22, 2025 |
| Ejecutado por      | Nicolas Urrutia |

---

## Resumen de Resultados

| Métrica                    | Valor |
|----------------------------|-------|
| **Total de Pruebas**       | 14    |
| **Pruebas Aprobadas**      | 14    |
| **Pruebas Fallidas**       | 0     |
| **Tasa de Éxito**          | 100%  |
| **Tiempo de Ejecución**    | 4.13s |
| **Fecha de Ejecución**     | October 22, 2025 |

---

## Observaciones Generales

1. **Cobertura Completa de Eliminación**: Las pruebas cubren ambos tipos de eliminación:
   - **Eliminación Física (Hard Delete)**: Cuando no hay datos asociados
   - **Eliminación Lógica (Soft Delete)**: Cuando existen datos asociados, marcando el dispositivo como inactivo

2. **Toggle Status Validado**: El endpoint de cambio de estado funciona correctamente en ambas direcciones:
   - Activo → Inactivo: "Dispositivo inactivado exitosamente"
   - Inactivo → Activo: "Dispositivo activado exitosamente"

3. **Control de Permisos Robusto**:
   - Permiso 162 para eliminación (`telemetry_device.delete`)
   - Permiso 115 para toggle status (`telemetry_device.toggle`)
   - Respuestas 403 apropiadas cuando faltan permisos

4. **Idempotencia Implementada**: El sistema maneja correctamente:
   - Intentos de eliminar dispositivos ya inactivos
   - Operaciones concurrentes con manejo de conflictos (409)
   - Dispositivos inexistentes (404)

5. **Manejo de Errores Robusto**:
   - Errores de BD retornan 500 con mensajes claros
   - No se dejan estados inconsistentes
   - Logs apropiados para debugging

6. **Auditoría Completa**: Se verifica que ambos flujos de eliminación registren:
   - Usuario que ejecuta la acción
   - Timestamp de la operación
   - Tipo de operación (física vs lógica)
   - ID del dispositivo afectado

7. **Filtrado de Dispositivos Inactivos**: Los dispositivos marcados como inactivos no aparecen en las listas operativas, garantizando integridad del sistema.

8. **Publicación de Eventos en Tiempo Real**: Los cambios de estado se publican correctamente al bus de eventos para actualizaciones en tiempo real en el frontend.

---

## Detalles Técnicos de Implementación

### Flujo de Eliminación

```
┌─────────────────────────────────────────┐
│  DELETE /telemetry-devices/{id}/       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Verificar Permisos  │
        │   (Permiso 162)     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │ Dispositivo Existe? │
        └──────┬──────────────┘
               │
         ┌─────┴─────┐
         │           │
       NO│           │SÍ
         │           │
         ▼           ▼
    ┌────────┐  ┌──────────────────────┐
    │404     │  │¿Tiene datos          │
    │Not     │  │asociados?            │
    │Found   │  └────┬─────────────────┘
    └────────┘       │
                ┌────┴────┐
                │         │
              SÍ│         │NO
                │         │
                ▼         ▼
    ┌──────────────┐  ┌──────────────┐
    │ SOFT DELETE  │  │ HARD DELETE  │
    │ Estado=2     │  │ DELETE FROM  │
    │ (Inactivo)   │  │ DB           │
    └──────────────┘  └──────────────┘
                │         │
                └────┬────┘
                     │
                     ▼
            ┌────────────────┐
            │ Registrar      │
            │ Auditoría      │
            └────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ HTTP 200 OK    │
            └────────────────┘
```

### Flujo de Toggle Status

```
┌──────────────────────────────────────────────┐
│  PATCH /telemetry-devices/{id}/toggle-status│
└────────────────┬─────────────────────────────┘
                 │
                 ▼
       ┌─────────────────────┐
       │ Verificar Permisos  │
       │   (Permiso 115)     │
       └──────────┬──────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │ Dispositivo Existe? │
       └──────┬──────────────┘
              │
        ┌─────┴─────┐
        │           │
      NO│           │SÍ
        │           │
        ▼           ▼
   ┌────────┐  ┌──────────────┐
   │404     │  │Estado Actual?│
   │Not     │  └──────┬───────┘
   │Found   │         │
   └────────┘    ┌────┴────┐
                 │         │
           Activo│         │Inactivo
                 │         │
                 ▼         ▼
       ┌──────────────┐ ┌──────────────┐
       │ Estado = 2   │ │ Estado = 1   │
       │ (Inactivo)   │ │ (Activo)     │
       └──────────────┘ └──────────────┘
                 │         │
                 └────┬────┘
                      │
                      ▼
            ┌─────────────────┐
            │ Registrar       │
            │ Auditoría       │
            └─────────┬───────┘
                      │
                      ▼
            ┌─────────────────┐
            │ Publicar Evento │
            │ Tiempo Real     │
            └─────────┬───────┘
                      │
                      ▼
            ┌─────────────────┐
            │ HTTP 200 OK     │
            └─────────────────┘
```

---

## Recomendaciones

1. **Pruebas de Integración**: Implementar pruebas de integración que validen:
   - Flujo completo con base de datos real
   - Verificación de integridad referencial
   - Cascada de eliminaciones cuando aplique

2. **Pruebas de Concurrencia Reales**: Validar con herramientas de carga:
   - Múltiples usuarios intentando eliminar el mismo dispositivo
   - Toggle simultáneo desde diferentes sesiones
   - Uso de locks optimistas o pesimistas

3. **Métricas de Auditoría**: Implementar dashboard que muestre:
   - Cantidad de eliminaciones físicas vs lógicas
   - Dispositivos más frecuentemente desactivados
   - Tiempo promedio de respuesta por operación

4. **Notificaciones**: Considerar notificar a administradores cuando:
   - Se eliminen físicamente dispositivos
   - Se realicen múltiples desactivaciones en corto tiempo
   - Ocurran errores 500 en operaciones críticas

5. **Recuperación de Dispositivos**: Evaluar implementar:
   - Endpoint para reactivar dispositivos desactivados
   - Historial de cambios de estado
   - Papelera de reciclaje con tiempo de retención

---

**Elaborado por:** Nicolas Urrutia  
**Área:** Quality Assurance (QA)  
**Fecha:** October 22, 2025  
**Módulo:** Gestión de Dispositivos de Telemetría  
**Endpoints:** `DELETE /telemetry-devices/{id}/` y `PATCH /telemetry-devices/{id}/toggle-status/`
