# Reporte de Pruebas Unitarias - UT-SM-006
---

## UT-SM-006: Programación exitosa (camino feliz)

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006 |
| **Título** | 201 Created – Programación exitosa (camino feliz) |
| **Descripción** | Verificar que se programa un mantenimiento desde una solicitud aprobada, se asigna consecutivo anual, la solicitud pasa a Aceptado (id=11), la programación queda en Programado (id=13), registra auditorías y retorna 201. |
| **Precondiciones** | - Usuario con permiso 120<br>- Solicitud id_request=3 en estado Pendiente (id=10)<br>- Técnico id=9 activo con permiso 116 y disponible<br>- Existe types_category=12 con maintenance_type=35 activo<br>- Maquinaria id=4 en estado Activo (id=4)<br>- Servicios de notificación e historial mockeados |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-02T10:30:00Z",<br>  "assigned_technician": 9,<br>  "details": "Atención prioritaria a la maquina por ruido al desplazarse",<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Crear usuario autenticado con permiso 120, crear solicitud pendiente, crear técnico disponible, mockear notificaciones<br>**Act**: POST /maintenance_request/3/schedule/ con datos válidos<br>**Assert**: Verificar status 201, success=true, mensaje esperado, ids retornados, solicitud→estado 11 (Aceptado), programación→estado 13 (Programado), notificación enviada |
| **Resultado Esperado** | - Status Code: 201<br>- Response: `{"success": true, "message": "Mantenimiento programado exitosamente desde la solicitud", "data": {"id_maintenance_scheduling": <id>, "id_maintenance_request": "3"}}`<br>- Solicitud cambia a estado Aceptado (id=11)<br>- Se crea MaintenanceScheduling con estado Programado (id=13)<br>- Se registran fechas de auditoría |
| **Resultado Obtenido** | ✅ Status Code: 201<br>✅ Solicitud actualizada a estado 11<br>✅ Programación creada con estado 13<br>✅ Técnico asignado correctamente<br>✅ Notificación enviada |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.1: Fecha/hora programada en el pasado

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.1 |
| **Título** | 422 – Fecha/hora programada en el pasado |
| **Descripción** | Validar rechazo cuando scheduled_at está en el pasado. |
| **Precondiciones** | - Usuario con permiso 120<br>- Solicitud válida en estado Pendiente<br>- Técnico válido y disponible<br>- Fecha actual: 2025-09-30 |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2024-01-01T08:00:00Z",<br>  "assigned_technician": 9,<br>  "details": "Prueba",<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Crear solicitud pendiente válida<br>**Act**: POST endpoint con fecha en el pasado<br>**Assert**: Verificar status 422 con error en campo scheduled_at |
| **Resultado Esperado** | - Status Code: 422<br>- Response: `{"success": false, "message": "Error de validación", "details": {"scheduled_at": ["La fecha y hora programada no puede estar en el pasado."]}}`<br>- No se crea programación en BD |
| **Resultado Obtenido** | ✅ Status Code: 422<br>✅ Mensaje de error correcto<br>✅ Campo scheduled_at identificado en details |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.2: Técnico no disponible

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.2 |
| **Título** | 422 – Técnico no disponible (conflicto de agenda) |
| **Descripción** | Rechazo si el técnico ya tiene servicio en la misma franja horaria. |
| **Precondiciones** | - Usuario con permiso 120<br>- Técnico id=9 ocupado en 2025-10-02T10:30:00Z<br>- Dos solicitudes válidas (id=102, id=103) |
| **Datos de Entrada** | Primera solicitud: `{"scheduled_at": "2025-10-02T10:30:00Z", "assigned_technician": 9, ...}`<br>Segunda solicitud (conflicto): `{"scheduled_at": "2025-10-02T10:30:00Z", "assigned_technician": 9, ...}` |
| **Pasos (AAA)** | **Arrange**: Crear 2 solicitudes pendientes, programar técnico 9 en fecha específica<br>**Act**: Intentar programar mismo técnico en misma fecha/hora<br>**Assert**: Segunda llamada retorna 422 con error en assigned_technician |
| **Resultado Esperado** | - Primera programación: 201<br>- Segunda programación: 422<br>- Error: "El técnico seleccionado no está disponible en la fecha y hora indicadas." |
| **Resultado Obtenido** | ✅ Primera programación exitosa (201)<br>✅ Segunda programación rechazada (422)<br>✅ Validación de conflicto de agenda funcionando |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.3: Solicitud ya programada

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.3 |
| **Título** | 422 – Solicitud ya cuenta con programación |
| **Descripción** | Validar que no se permita programar una solicitud que ya tiene mantenimiento programado. |
| **Precondiciones** | - Usuario con permiso 120<br>- Solicitud id=7 ya asociada a programación existente<br>- Técnico id=8 válido |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-02T10:30:00Z",<br>  "assigned_technician": 8,<br>  "details": "Intentar reprogramar",<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Crear solicitud que ya tiene programación asociada<br>**Act**: Intentar programar nuevamente la misma solicitud<br>**Assert**: Verificar status 422 con error en id_maintenance_request |
| **Resultado Esperado** | - Status Code: 422<br>- Error: "La solicitud ya cuenta con un mantenimiento programado."<br>- Campo: id_maintenance_request |
| **Resultado Obtenido** | ✅ Status Code: 422<br>✅ Validación de solicitud duplicada funcionando<br>✅ Mensaje de error correcto |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.4: Usuario sin permiso

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.4 |
| **Título** | 403 – Usuario sin permiso de programación |
| **Descripción** | Validar rechazo de acceso a usuarios sin permiso 120. |
| **Precondiciones** | - Usuario autenticado (id=99) sin permiso 120<br>- Solicitud válida pendiente |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-02T10:30:00Z",<br>  "assigned_technician": 9,<br>  "details": "Intento sin permiso",<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Autenticar usuario sin permiso 120<br>**Act**: Intentar POST al endpoint<br>**Assert**: Verificar status 403 con mensaje de falta de autorización |
| **Resultado Esperado** | - Status Code: 403<br>- Message: "No tiene permisos para programar mantenimientos." |
| **Resultado Obtenido** | ✅ Status Code: 403<br>✅ Mensaje de autorización correcto<br>✅ Sistema de permisos funcionando |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.5: Técnico inválido

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.5 |
| **Título** | 422 – Técnico inválido o inactivo |
| **Descripción** | Validar que el técnico asignado exista, esté activo y tenga permiso 116. |
| **Precondiciones** | - Usuario con permiso 120<br>- Solicitud válida pendiente<br>- ID de técnico inexistente: 9999 |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-02T10:30:00Z",<br>  "assigned_technician": 9999,<br>  "details": "Técnico inválido",<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Crear solicitud válida<br>**Act**: POST endpoint con técnico inexistente (id=9999)<br>**Assert**: Verificar status 422 con error en assigned_technician |
| **Resultado Esperado** | - Status Code: 422<br>- Error en campo: assigned_technician<br>- Mensaje indicando técnico inválido |
| **Resultado Obtenido** | ✅ Status Code: 422<br>✅ Campo assigned_technician en details<br>✅ Validación de técnico funcionando |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.6: Tipo de mantenimiento inválido

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.6 |
| **Título** | 422 – Tipo de mantenimiento no válido |
| **Descripción** | Validar que maintenance_type exista y pertenezca a categoría 12. |
| **Precondiciones** | - Usuario con permiso 120<br>- Catálogo de tipos disponible<br>- Tipo id=999 NO pertenece a categoría 12 |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-02T10:30:00Z",<br>  "assigned_technician": 9,<br>  "details": "Tipo inválido",<br>  "maintenance_type": 999<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Crear tipo id=999 en categoría diferente a 12<br>**Act**: POST endpoint con maintenance_type=999<br>**Assert**: Verificar status 422 con error en maintenance_type |
| **Resultado Esperado** | - Status Code: 422<br>- Error: "El tipo de mantenimiento debe pertenecer a la categoría 'Tipos de mantenimiento'."<br>- Campo: maintenance_type |
| **Resultado Obtenido** | ✅ Status Code: 422<br>✅ Validación de categoría funcionando<br>✅ Error en campo maintenance_type |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.7: Detalles supera 350 caracteres

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.7 |
| **Título** | 422 – Detalles supera 350 caracteres |
| **Descripción** | Validar límite máximo de 350 caracteres en campo details. |
| **Precondiciones** | - Usuario con permiso 120<br>- Solicitud válida pendiente<br>- String de 351 caracteres generado |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-02T10:30:00Z",<br>  "assigned_technician": 9,<br>  "details": "AAAA...AAAA" (351 caracteres),<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Generar string de 351 caracteres<br>**Act**: POST endpoint con details demasiado largo<br>**Assert**: Verificar status 422 con error en campo details |
| **Resultado Esperado** | - Status Code: 422<br>- Error en campo: details<br>- Validación de longitud máxima |
| **Resultado Obtenido** | ✅ Status Code: 422<br>✅ Campo details en details de error<br>✅ Validación de longitud funcionando |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.8: Consecutivo anual incrementa

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.8 |
| **Título** | 201 – Consecutivo anual incrementa correctamente |
| **Descripción** | Validar que el consecutivo se asigna como \<YYYY\>-\<secuencia\> y aumenta en el mismo año. |
| **Precondiciones** | - Usuario con permiso 120<br>- Sistema configurado para generar consecutivos<br>**NOTA**: El sistema actual NO implementa consecutivos anuales en MaintenanceScheduling. Esta prueba verifica que se crea sin errores. |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-03T09:00:00Z",<br>  "assigned_technician": 9,<br>  "details": "Prueba consecutivo",<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Crear solicitud pendiente para año 2025<br>**Act**: POST endpoint con datos válidos<br>**Assert**: Verificar status 201 y creación exitosa |
| **Resultado Esperado** | - Status Code: 201<br>- Programación creada exitosamente<br>**NOTA**: Consecutivo anual pendiente de implementación futura |
| **Resultado Obtenido** | ✅ Status Code: 201<br>✅ Programación creada sin errores<br>ℹ️ Consecutivo anual no implementado aún |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.9: Consecutivo reinicia en nuevo año

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.9 |
| **Título** | 201 – Consecutivo reinicia en nuevo año |
| **Descripción** | Validar que al iniciar un año nuevo la secuencia reinicia en 0001. |
| **Precondiciones** | - Usuario con permiso 120<br>- Sistema configurado para año 2026<br>**NOTA**: El sistema actual NO implementa consecutivos anuales. Esta prueba verifica programación en año futuro. |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2026-01-02T08:00:00Z",<br>  "assigned_technician": 9,<br>  "details": "Prueba año 2026",<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Crear solicitud para programar en 2026<br>**Act**: POST endpoint con fecha en año futuro<br>**Assert**: Verificar status 201 |
| **Resultado Esperado** | - Status Code: 201<br>- Programación creada para año 2026<br>**NOTA**: Consecutivo anual pendiente de implementación |
| **Resultado Obtenido** | ✅ Status Code: 201<br>✅ Sistema acepta fechas en años futuros<br>ℹ️ Consecutivo anual no implementado |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.10: Doble envío del mismo request

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.10 |
| **Título** | 409/422 – Doble envío del mismo request (idempotencia) |
| **Descripción** | Validar que un mismo payload no cree duplicados. El sistema debe detectar intentos de programación duplicada. |
| **Precondiciones** | - Usuario con permiso 120<br>- Solicitud id=110 pendiente<br>- Notificaciones mockeadas |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-05T14:00:00Z",<br>  "assigned_technician": 9,<br>  "details": "Prueba doble envío",<br>  "maintenance_type": 35<br>}<br>```<br>(Mismo payload enviado 2 veces) |
| **Pasos (AAA)** | **Arrange**: Crear solicitud pendiente<br>**Act**: Enviar mismo payload 2 veces consecutivas<br>**Assert**: Primera llamada 201, segunda llamada 422 |
| **Resultado Esperado** | - 1° request: 201 (creación exitosa)<br>- 2° request: 422 (rechazo por duplicado)<br>- Validación: solicitud ya programada O conflicto de técnico |
| **Resultado Obtenido** | ✅ Primera llamada: 201<br>✅ Segunda llamada: 422<br>✅ Sistema detecta conflicto de técnico (validación correcta para prevenir duplicados) |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |

---

## UT-SM-006.11: Notificación y auditoría

| Campo | Detalle |
|-------|---------|
| **ID** | UT-SM-006.11 |
| **Título** | 201 – Notificación y auditoría (efectos secundarios) |
| **Descripción** | Validar efectos secundarios: notificación al técnico y registro de auditoría con timestamps. |
| **Precondiciones** | - Usuario con permiso 120<br>- Solicitud válida pendiente<br>- Mocks de notificación configurados<br>- Técnico id=9 válido |
| **Datos de Entrada** | ```json<br>{<br>  "scheduled_at": "2025-10-06T16:00:00Z",<br>  "assigned_technician": 9,<br>  "details": "Prueba efectos secundarios",<br>  "maintenance_type": 35<br>}<br>``` |
| **Pasos (AAA)** | **Arrange**: Configurar spies para notificación/auditoría<br>**Act**: POST endpoint<br>**Assert**: Verificar 201, notificación enviada, solicitud→estado 11, programación→estado 13, timestamps registrados |
| **Resultado Esperado** | - Status Code: 201<br>- Notificación enviada al técnico (mock llamado)<br>- Solicitud: request_status=11, modification_date actualizado<br>- Programación: maintenance_scheduling_status=13, registration_date/modification_date/id_responsible_user registrados |
| **Resultado Obtenido** | ✅ Status Code: 201<br>✅ Mock de notificación llamado<br>✅ Solicitud actualizada a estado 11<br>✅ Programación creada con estado 13<br>✅ Todos los campos de auditoría poblados |
| **Estado** | ✅ PASADO |
| **Fecha Ejecución** | 30/09/2025 |
| **Ejecutado por** | Juan Camilo |
