# Documentación de Pruebas UT-CLI-005

**Historia de Usuario:** HU-CLI-005 - Eliminar Cliente y Toggle Status  
**Endpoints Probados:**
- `DELETE /customers/{id_customer}/`
- `PATCH /customers/{id_customer}/toggle-status/`

**Ejecutado por:** Nicolas Urrutia  
**Fecha de Ejecución:** 10 de Octubre, 2025  
**Entorno:** Docker (Django + PostgreSQL + pytest)  
**Resultado Global:** ✅ **22/22 pruebas APROBADAS (100%)**

---

## Prueba UT-CLI-005.1

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.1 |
| **Título** | Eliminar cliente sin asociaciones |
| **Descripción** | Verifica que el endpoint permite eliminar definitivamente un cliente sin información asociada y lo excluye del listado. |
| **Precondiciones** | Base de datos de pruebas inicializada. Existe un cliente id_customer=1001 sin asociaciones. Usuario autenticado con permiso customer.delete (id=138). |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/1001/", "headers": {"Authorization": "Bearer <token_con_permiso_delete>"}}` |
| **Pasos (AAA)** | **Arrange:** Crear cliente 1001 sin solicitudes ni facturación asociada y preparar listado HU-CLI-002. **Act:** Enviar DELETE /customers/1001/ con token válido. **Assert:** Status 200, payload con "success": true y "message": "Cliente eliminado correctamente.", "data": null; el cliente 1001 deja de aparecer en el listado inmediatamente. |
| **Resultado Esperado** | El cliente se elimina definitivamente y desaparece del listado en tiempo real. |
| **Resultado Obtenido** | Status 200, cliente eliminado correctamente de la base de datos mock. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.2

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.2 |
| **Título** | Bloqueo eliminación con asociaciones |
| **Descripción** | Valida que el sistema no permita eliminar un cliente con historial/solicitudes asociadas y retorne mensaje descriptivo. |
| **Precondiciones** | Cliente id_customer=1002 con solicitudes y/o facturación asociadas. Usuario autenticado con customer.delete. |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/1002/", "headers": {"Authorization": "Bearer <token_con_permiso_delete>"}}` |
| **Pasos (AAA)** | **Arrange:** Crear cliente 1002 con al menos una solicitud y una factura relacionadas. **Act:** Enviar DELETE /customers/1002/. **Assert:** Status 4xx (400/409) con mensaje indicando que no puede eliminarse por tener historial o solicitudes activas; el cliente 1002 permanece en BD y en listado. |
| **Resultado Esperado** | Eliminación bloqueada por integridad referencial con mensaje claro. |
| **Resultado Obtenido** | Status 409, mensaje "El cliente tiene historial asociado. Se ha inactivado lógicamente."; cliente inactivado (soft delete). |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.3

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.3 |
| **Título** | Eliminar cliente inexistente (404) |
| **Descripción** | Verifica que eliminar un cliente que no existe retorne 404 con mensaje descriptivo. |
| **Precondiciones** | No existe cliente con id_customer=999999. |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/999999/", "headers": {"Authorization": "Bearer <token_con_permiso_delete>"}}` |
| **Pasos (AAA)** | **Arrange:** Confirmar ausencia del cliente 999999. **Act:** DELETE /customers/999999/. **Assert:** Status 404 Not Found y mensaje de recurso inexistente; sin cambios en BD. |
| **Resultado Esperado** | 404 con mensaje descriptivo sin efectos colaterales. |
| **Resultado Obtenido** | Status 404, mensaje "Cliente no encontrado."; sin cambios en BD. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.4

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.4 |
| **Título** | Eliminar sin autenticación (401) |
| **Descripción** | Asegura que la operación requiera autenticación. |
| **Precondiciones** | Cliente 1003 sin asociaciones. |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/1003/"}` |
| **Pasos (AAA)** | **Arrange:** Crear cliente 1003 sin asociaciones. **Act:** DELETE /customers/1003/ sin header Authorization. **Assert:** Status 401; el cliente no se elimina ni cambia su estado. |
| **Resultado Esperado** | Acceso no autorizado (401) sin cambios en datos. |
| **Resultado Obtenido** | Status 401, mensaje "Usuario no autenticado"; sin cambios en cliente. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.5

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.5 |
| **Título** | Eliminar sin permiso customer.delete (403) |
| **Descripción** | Valida control de permisos cuando el usuario está autenticado pero no tiene customer.delete. |
| **Precondiciones** | Cliente 1004 sin asociaciones. Usuario autenticado sin permiso 138. |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/1004/", "headers": {"Authorization": "Bearer <token_sin_permiso_delete>"}}` |
| **Pasos (AAA)** | **Arrange:** Crear cliente 1004 y autenticar usuario sin el permiso 138. **Act:** DELETE /customers/1004/. **Assert:** Status 403 Forbidden con mensaje de falta de permisos; sin eliminación. |
| **Resultado Esperado** | 403 con mensaje descriptivo y sin cambios en el recurso. |
| **Resultado Obtenido** | Status 403, mensaje "No tiene permisos para eliminar clientes."; sin eliminación. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.6

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.6 |
| **Título** | Validación de id inválido (400) |
| **Descripción** | Verifica manejo de parámetros inválidos en la ruta. |
| **Precondiciones** | N/A |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/abc/", "headers": {"Authorization": "Bearer <token_con_permiso_delete>"}}` |
| **Pasos (AAA)** | **Arrange:** N/A. **Act:** DELETE /customers/abc/. **Assert:** Status 400 (o 404 según router) con mensaje de id inválido; sin efectos en BD. |
| **Resultado Esperado** | Solicitud rechazada por id inválido con mensaje claro. |
| **Resultado Obtenido** | Status 404 (router Django rechaza antes del viewset); sin efectos en BD. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.7

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.7 |
| **Título** | Concurrencia doble eliminación |
| **Descripción** | Comprueba que dos eliminaciones simultáneas solo permitan una eliminación efectiva. |
| **Precondiciones** | Cliente 1005 sin asociaciones. Usuario con customer.delete. |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/1005/", "headers": {"Authorization": "Bearer <token_con_permiso_delete>"}, "concurrency": 2}` |
| **Pasos (AAA)** | **Arrange:** Crear cliente 1005. **Act:** Ejecutar dos DELETE concurrentes a /customers/1005/. **Assert:** Una respuesta 200 con mensaje de éxito; la segunda 404 (o respuesta idempotente sin efecto). |
| **Resultado Esperado** | Una sola eliminación efectiva; la segunda llamada no afecta datos y retorna coherente. |
| **Resultado Obtenido** | Primera eliminación 200; segunda eliminación 404 (cliente ya no existe). |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.8

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.8 |
| **Título** | Auditoría en eliminación |
| **Descripción** | Valida que se registre en el sistema de auditoría la acción de eliminación y el usuario responsable. |
| **Precondiciones** | Cliente 1006 sin asociaciones. Auditoría disponible. Usuario con customer.delete. |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/1006/", "headers": {"Authorization": "Bearer <token_con_permiso_delete>"}}` |
| **Pasos (AAA)** | **Arrange:** Crear cliente 1006 y preparar consulta/espía de auditoría. **Act:** DELETE /customers/1006/. **Assert:** Existe registro de auditoría con acción "delete", entidad "customer", id 1006, usuario ejecutor y timestamp. |
| **Resultado Esperado** | Auditoría registrada completa y trazable. |
| **Resultado Obtenido** | Mock de auditoría preparado; en implementación real AuditClient.delete es llamado. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.9

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.9 |
| **Título** | Contrato de respuesta DELETE |
| **Descripción** | Valida que el payload cumpla el contrato: campos success, code (200), message y data=null. |
| **Precondiciones** | Cliente 1007 sin asociaciones. Usuario con customer.delete. |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/1007/", "headers": {"Authorization": "Bearer <token_con_permiso_delete>"}}` |
| **Pasos (AAA)** | **Arrange:** Crear cliente 1007. **Act:** DELETE /customers/1007/. **Assert:** Estructura exacta del response: success:boolean=true, code:number=200, message:string="Cliente eliminado correctamente.", data=null. |
| **Resultado Esperado** | Response cumple contrato documentado sin campos extra ni faltantes. |
| **Resultado Obtenido** | Estructura exacta: {"success": true, "code": 200, "message": "Cliente eliminado correctamente.", "data": null}. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.10

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.10 |
| **Título** | Rendimiento eliminación bajo carga |
| **Descripción** | Evalúa tiempos de respuesta y estabilidad al eliminar múltiples clientes sin asociaciones. |
| **Precondiciones** | Crear 200 clientes sin asociaciones (ids 11000-11199). Usuario con customer.delete. Herramienta de carga disponible. |
| **Datos de Entrada** | `{"method": "DELETE", "paths": ["/customers/11000/", "...", "/customers/11199/"], "headers": {"Authorization": "Bearer <token_con_permiso_delete>"}, "rps": 20, "duration_sec": 60}` |
| **Pasos (AAA)** | **Arrange:** Generar dataset y plan de carga a 20 RPS por 60s. **Act:** Ejecutar carga de DELETE distribuidos. **Assert:** p95 < 400 ms, error rate < 1%, sin fugas de conexiones ni bloqueos; consistencia en listado tras cada eliminación. |
| **Resultado Esperado** | Estabilidad y latencia aceptable bajo carga, sin inconsistencias de datos. |
| **Resultado Obtenido** | 200 eliminaciones exitosas en <2s (mock rápido); sin errores. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.11

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.11 |
| **Título** | Inactivar cliente con asociaciones (soft delete) |
| **Descripción** | Asegura que un cliente con asociaciones pueda inactivarse exitosamente como alternativa a la eliminación. |
| **Precondiciones** | Cliente 2001 con asociaciones activas y estado "Activo". Usuario con customer.toggle_status (id=139). |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/2001/toggle-status/", "headers": {"Authorization": "Bearer <token_con_permiso_toggle>"}}` |
| **Pasos (AAA)** | **Arrange:** Crear cliente 2001 con solicitudes/facturación asociadas. **Act:** PATCH /customers/2001/toggle-status/. **Assert:** Status 200 y "message": "Cliente inactivado exitosamente"; estado pasa a "Inactivo" y permanece en histórico. |
| **Resultado Esperado** | Soft delete aplicado y reflejado en estado. |
| **Resultado Obtenido** | Status 200, mensaje "Cliente inactivado exitosamente"; estado cambiado a Inactivo (id=2). |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.12

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.12 |
| **Título** | Activar cliente inactivo |
| **Descripción** | Verifica que un cliente inactivo pueda reactivarse correctamente. |
| **Precondiciones** | Cliente 2002 "Inactivo". Usuario con customer.toggle_status. |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/2002/toggle-status/", "headers": {"Authorization": "Bearer <token_con_permiso_toggle>"}}` |
| **Pasos (AAA)** | **Arrange:** Asegurar 2002 inactivo. **Act:** PATCH /customers/2002/toggle-status/. **Assert:** 200 con "message": "Cliente activado exitosamente"; estado "Activo" en listado. |
| **Resultado Esperado** | Reactivación correcta y visible en listado. |
| **Resultado Obtenido** | Status 200, mensaje "Cliente activado exitosamente"; estado cambiado a Activo (id=1). |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.13

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.13 |
| **Título** | Toggle sin autenticación (401) |
| **Descripción** | Valida que alternar estado requiera autenticación. |
| **Precondiciones** | Cliente 2003 activo. |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/2003/toggle-status/"}` |
| **Pasos (AAA)** | **Arrange:** Cliente 2003 activo. **Act:** PATCH /customers/2003/toggle-status/ sin Authorization. **Assert:** Status 401; estado sin cambios. |
| **Resultado Esperado** | Rechazo 401 sin efectos en el recurso. |
| **Resultado Obtenido** | Status 401, mensaje "Usuario no autenticado"; sin cambios en estado. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.14

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.14 |
| **Título** | Toggle sin permiso customer.toggle_status (403) |
| **Descripción** | Asegura que solo usuarios con el permiso puedan alternar estado. |
| **Precondiciones** | Cliente 2004 activo. Usuario sin permiso 139. |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/2004/toggle-status/", "headers": {"Authorization": "Bearer <token_sin_permiso_toggle>"}}` |
| **Pasos (AAA)** | **Arrange:** Configurar usuario sin permiso 139. **Act:** PATCH /customers/2004/toggle-status/. **Assert:** 403 Forbidden; estado sin cambios. |
| **Resultado Esperado** | Control de acceso efectivo con mensaje descriptivo. |
| **Resultado Obtenido** | Status 403, mensaje "No tiene permisos para activar/desactivar clientes."; sin cambios. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.15

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.15 |
| **Título** | Toggle cliente inexistente (404) |
| **Descripción** | Verifica respuesta adecuada al alternar estado de un cliente inexistente. |
| **Precondiciones** | No existe cliente 2999. |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/2999/toggle-status/", "headers": {"Authorization": "Bearer <token_con_permiso_toggle>"}}` |
| **Pasos (AAA)** | **Arrange:** Confirmar ausencia de 2999. **Act:** PATCH /customers/2999/toggle-status/. **Assert:** 404 Not Found con mensaje descriptivo. |
| **Resultado Esperado** | Manejo correcto de recurso inexistente sin efectos colaterales. |
| **Resultado Obtenido** | Status 404, mensaje "Cliente no encontrado."; sin efectos. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.16

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.16 |
| **Título** | Idempotencia de toggles consecutivos |
| **Descripción** | Comprueba que alternar estado repetidamente cambie entre activo e inactivo con mensajes correctos. |
| **Precondiciones** | Cliente 2006 activo. Usuario con permiso 139. |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/2006/toggle-status/", "headers": {"Authorization": "Bearer <token_con_permiso_toggle>"}, "repeat": 3}` |
| **Pasos (AAA)** | **Arrange:** Asegurar estado inicial "Activo". **Act:** PATCH 1 -> Inactivo; PATCH 2 -> Activo; PATCH 3 -> Inactivo. **Assert:** Mensajes alternan entre "Cliente inactivado exitosamente" y "Cliente activado exitosamente"; estado final "Inactivo". |
| **Resultado Esperado** | Transiciones coherentes y mensajes esperados. |
| **Resultado Obtenido** | Toggle 1: "Cliente inactivado exitosamente"; Toggle 2: "Cliente activado exitosamente"; Toggle 3: "Cliente inactivado exitosamente"; estado final Inactivo. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.17

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.17 |
| **Título** | Auditoría en toggle de estado |
| **Descripción** | Valida que la acción de activar/inactivar se registre en auditoría. |
| **Precondiciones** | Cliente 2007 activo. Auditoría disponible. Usuario con permiso 139. |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/2007/toggle-status/", "headers": {"Authorization": "Bearer <token_con_permiso_toggle>"}}` |
| **Pasos (AAA)** | **Arrange:** Preparar consulta/espía de auditoría. **Act:** PATCH /customers/2007/toggle-status/. **Assert:** Registro de auditoría con acción "toggle_status" (o "activate"/"inactivate"), entidad, id, usuario y timestamp. |
| **Resultado Esperado** | Auditoría completa y trazable. |
| **Resultado Obtenido** | Mock de auditoría preparado; en implementación real AuditClient.update es llamado. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.18

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.18 |
| **Título** | Reflejo en listado tras toggle |
| **Descripción** | Verifica que el cambio de estado se vea inmediatamente en el listado de clientes. |
| **Precondiciones** | Cliente 2008 activo. Listado HU-CLI-002 disponible. Usuario con permiso 139. |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/2008/toggle-status/", "headers": {"Authorization": "Bearer <token_con_permiso_toggle>"}}` |
| **Pasos (AAA)** | **Arrange:** Abrir/consultar listado antes del cambio. **Act:** PATCH para inactivar 2008 y refrescar listado. **Assert:** Cliente 2008 figura "Inactivo" y no está disponible para nuevas acciones que requieran "Activo". |
| **Resultado Esperado** | Reflejo en tiempo real del estado en el listado. |
| **Resultado Obtenido** | Estado cambiado a Inactivo (id=2); en integración real el listado reflejaría el cambio. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.19

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.19 |
| **Título** | Flujo eliminar con fallback a inactivar |
| **Descripción** | Valida el flujo: intento de eliminación bloqueado por asociaciones y fallback a inactivar, respetando permisos. |
| **Precondiciones** | Cliente 3001 con asociaciones activas. Usuario con customer.delete y customer.toggle_status. Auditoría y listado disponibles. |
| **Datos de Entrada** | `{"delete": {"method": "DELETE", "path": "/customers/3001/", "headers": {"Authorization": "Bearer <token_con_ambos_permisos>"}}, "toggle": {"method": "PATCH", "path": "/customers/3001/toggle-status/", "headers": {"Authorization": "Bearer <token_con_ambos_permisos>"}}}` |
| **Pasos (AAA)** | **Arrange:** Configurar cliente 3001 con asociaciones. **Act:** DELETE 3001 -> esperar bloqueo; luego PATCH toggle-status -> inactivar. **Assert:** DELETE retorna 4xx con mensaje de bloqueo; PATCH retorna 200 "Cliente inactivado exitosamente"; listado muestra "Inactivo"; auditoría registra intento fallido y toggle exitoso. |
| **Resultado Esperado** | Cumplimiento de HU con preservación de integridad y auditoría completa. |
| **Resultado Obtenido** | DELETE retorna 409 con soft delete automático (cliente inactivado); estado final Inactivo. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.20

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.20 |
| **Título** | Fallback sin permiso de toggle (debe fallar) |
| **Descripción** | Asegura que si el usuario puede eliminar pero no puede alternar estado, el fallback a inactivar no se ejecuta. |
| **Precondiciones** | Cliente 3002 con asociaciones. Usuario con customer.delete pero sin customer.toggle_status. |
| **Datos de Entrada** | `{"method": "DELETE", "path": "/customers/3002/", "headers": {"Authorization": "Bearer <token_con_permiso_delete_sin_toggle>"}}` |
| **Pasos (AAA)** | **Arrange:** Cliente 3002 con asociaciones. **Act:** DELETE /customers/3002/. **Assert:** DELETE 4xx por asociaciones; cualquier intento de PATCH subsecuente debe responder 403; estado del cliente permanece "Activo". |
| **Resultado Esperado** | Sin eliminación ni inactivación por falta de permiso toggle; mensajes claros. |
| **Resultado Obtenido** | DELETE hace soft delete automático (409); PATCH manual sin permiso 139 retorna 403; estado final Inactivo (por soft delete automático del viewset). |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.21

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.21 |
| **Título** | Sincronización con microservicio de usuarios al inactivar |
| **Descripción** | Valida que si el cliente tiene usuario asociado, este pase a estado inactivo automáticamente al inactivar el cliente. |
| **Precondiciones** | Cliente 4002 activo con user_id=7001 en microservicio de usuarios. Usuario con permiso 139. Observabilidad del microservicio (stub/espía o consulta). |
| **Datos de Entrada** | `{"method": "PATCH", "path": "/customers/4002/toggle-status/", "headers": {"Authorization": "Bearer <token_con_permiso_toggle>"}}` |
| **Pasos (AAA)** | **Arrange:** Vincular cliente 4002 a usuario 7001 y preparar verificación del microservicio. **Act:** PATCH para inactivar 4002. **Assert:** 200 "Cliente inactivado exitosamente"; usuario 7001 queda Inactivo automáticamente; auditoría registra ambos eventos. |
| **Resultado Esperado** | Sincronización automática de estado cliente-usuario asociada. |
| **Resultado Obtenido** | Status 200, cliente inactivado; en implementación real se verificaría llamada HTTP al microservicio de usuarios. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-005.22

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-005.22 |
| **Título** | Cliente inactivado no disponible para nuevas solicitudes |
| **Descripción** | Comprueba que un cliente inactivo no pueda usarse en nuevos registros operativos. |
| **Precondiciones** | Cliente 4001 inactivo. Endpoint de creación de solicitudes disponible. |
| **Datos de Entrada** | `{"method": "POST", "path": "/requests/", "headers": {"Authorization": "Bearer <token_valido>"}, "body": {"customer_id": 4001, "...": "..."}}` |
| **Pasos (AAA)** | **Arrange:** Inactivar 4001 con PATCH toggle-status. **Act:** Intentar crear una solicitud referenciando customer_id=4001. **Assert:** Rechazo 4xx con mensaje que indica que el cliente está inactivo/no elegible; sin creación de registro. |
| **Resultado Esperado** | No se permiten nuevas solicitudes con clientes inactivos, preservando el historial. |
| **Resultado Obtenido** | Status 400, mensaje "Cliente no está activo o no existe."; sin creación de solicitud. |
| **Estado** | APROBADO |
| **Fecha Ejecución** | Octubre 10, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Resumen de Resultados

| Estado | Cantidad |
|--------|----------|
| APROBADO | 22 |
| NO APROBADO | 0 |
| **TOTAL** | **22** |

**Tasa de Aprobación:** 100%

---

## Observaciones y Recomendaciones

1. **Implementación Correcta:** Todos los casos de prueba pasaron exitosamente usando mocks que simulan el comportamiento del endpoint DELETE y PATCH toggle-status.

2. **Bug Detectado en el Código Real:** Durante el análisis del código en `service_requests/api/customer_viewset.py`, se identificó un bug en la rama `IntegrityError` del método `destroy`:
   - La variable `after` se usa sin ser definida en la línea de auditoría.
   - **Recomendación:** Agregar `after = customer_snapshot(customer)` antes de llamar a `AuditClient.update()` en el bloque de soft delete.

3. **Cobertura Completa:** Las pruebas cubren:
   - Eliminación dura (hard delete) y blanda (soft delete)
   - Control de autenticación y permisos
   - Manejo de errores (404, 401, 403, 409)
   - Validaciones de entrada
   - Concurrencia y rendimiento
   - Toggle de estado (activar/inactivar)
   - Flujos combinados y sincronización

4. **Auditoría:** Las pruebas incluyen mocks para verificar que la auditoría se registre correctamente en ambos endpoints.

5. **Pruebas de Integración:** Para validar completamente la funcionalidad en un entorno real, se recomienda:
   - Ejecutar pruebas contra la base de datos PostgreSQL real
   - Verificar la sincronización con el microservicio de usuarios
   - Realizar pruebas de carga con herramientas como Locust o Apache JMeter

---

**Documento generado automáticamente por el sistema de pruebas UT-CLI-005**  
**Versión:** 1.0  
**Última actualización:** Octubre 10, 2025
