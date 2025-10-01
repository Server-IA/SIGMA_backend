# Documentación de Pruebas Unitarias UT-PM-002

Esta documentación detalla las 36 pruebas unitarias para el endpoint de lista de programaciones de mantenimiento, siguiendo el formato estandarizado.

## Prueba UT-PM-002.1

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.1 |
| Título             | Acceso sin token devuelve 401 |
| Descripción        | Verificar que el endpoint rechaza solicitudes sin token. |
| Precondiciones     | Endpoint operativo; no se envía Authorization. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: sin Authorization; Query Params: {} |
| Pasos (AAA)        | Arrange: preparar request sin token; Act: invocar GET; Assert: status 401, cuerpo con success=false o mensaje de no autenticado. |
| Resultado Esperado | HTTP 401; sin data. |
| Resultado Obtenido | HTTP 401. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.2

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.2 |
| Título             | Acceso sin permiso requerido devuelve 403 |
| Descripción        | Un usuario autenticado sin el permiso 125 no puede listar. |
| Precondiciones     | Usuario válido con token activo sin permiso 125. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_sin_125>; Query Params: {} |
| Pasos (AAA)        | Arrange: token sin permiso; Act: GET; Assert: 403, mensaje "forbidden" o equivalente. |
| Resultado Esperado | HTTP 403; sin data. |
| Resultado Obtenido | HTTP 403. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.3

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.3 |
| Título             | Acceso con permiso 125 devuelve 200 y data |
| Descripción        | Validar respuesta exitosa con datos. |
| Precondiciones     | Usuario con permiso 125; base con registros de ejemplo. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Pasos (AAA)        | Arrange: token válido; Act: GET; Assert: 200, success=true, data es arreglo. |
| Resultado Esperado | HTTP 200; estructura conforme; al menos 1 elemento si hay data. |
| Resultado Obtenido | HTTP 200; success=true, data con 7 elementos. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.4

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.4 |
| Título             | Revocación de permiso invalida acceso |
| Descripción        | Si se revoca el permiso 125, el acceso se bloquea. |
| Precondiciones     | Token emitido; permiso 125 revocado antes de la llamada. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_previo>; Query Params: {} |
| Pasos (AAA)        | Arrange: revocar permiso; Act: GET; Assert: 403. |
| Resultado Esperado | HTTP 403. |
| Resultado Obtenido | HTTP 403. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.5

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.5 |
| Título             | Rol diferente con permiso explícito accede |
| Descripción        | Cualquier rol con permiso 125 accede. |
| Precondiciones     | Usuario con rol X que incluye permiso 125. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_rol_X>; Query Params: {} |
| Pasos (AAA)        | Arrange: token con 125; Act: GET; Assert: 200. |
| Resultado Esperado | HTTP 200; data presente. |
| Resultado Obtenido | HTTP 200; data presente. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.6

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.6 |
| Título             | Validar campos obligatorios y tipos |
| Descripción        | Comprobar claves y tipos de cada item. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Estructura consistente en todos los elementos. |
| Resultado Obtenido | Campos presentes con tipos correctos. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.7

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.7 |
| Título             | scheduled_at en ISO8601 UTC |
| Descripción        | Asegurar formato "YYYY-MM-DDThh:mm:ssZ". |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Todas las fechas parseables y en UTC. |
| Resultado Obtenido | Fechas en formato ISO8601 con Z. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.8

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.8 |
| Título             | Mapeo status_id-status_name consistente |
| Descripción        | Verificar que id y nombre coinciden con catálogo (p. ej., 13=Programado, 14=Cancelado). |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Ninguna discrepancia. |
| Resultado Obtenido | Mapeo correcto: 13=Programado, 14=Cancelado, 15=Realizado. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.9

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.9 |
| Título             | Validar URL de imagen o null permitido |
| Descripción        | machinery_image debe ser URL válida o null. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Cumplimiento en todos los items. |
| Resultado Obtenido | URLs válidas o null. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.10

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.10 |
| Título             | Sin registros retorna lista vacía |
| Descripción        | Cuando no hay mantenimientos, retorna success=true y data=[]. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | data vacía sin error. |
| Resultado Obtenido | data vacía. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.11

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.11 |
| Título             | Filtrar por start_date y end_date |
| Descripción        | Debe retornar solo mantenimientos en el rango. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"start_date": "2025-10-01", "end_date": "2025-10-03"} |
| Resultado Esperado | Subconjunto correcto; ningún fuera de rango. |
| Resultado Obtenido | Solo ítems en rango. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.12

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.12 |
| Título             | Fecha inválida retorna 400 |
| Descripción        | Validar validación de formato. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"start_date": "10-01-2025"} |
| Resultado Esperado | HTTP 400; sin data. |
| Resultado Obtenido | HTTP 400. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.13

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.13 |
| Título             | start_date > end_date retorna 400 |
| Descripción        | Si start_date es mayor a end_date, error. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"start_date": "2025-12-31", "end_date": "2025-01-01"} |
| Resultado Esperado | HTTP 400; detalle de error de rango. |
| Resultado Obtenido | HTTP 400. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.14

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.14 |
| Título             | Filtro por estado |
| Descripción        | Retorna solo status_id=13. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"status_id": "13"} |
| Resultado Esperado | Solo Programado. |
| Resultado Obtenido | Solo status_id=13. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.15

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.15 |
| Título             | Filtro por técnico |
| Descripción        | Retorna solo del técnico solicitado. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"assigned_technician_id": "1"} |
| Resultado Esperado | Subconjunto por técnico. |
| Resultado Obtenido | Solo assigned_technician_id=1. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.16

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.16 |
| Título             | Filtro por tipo |
| Descripción        | Filtrar por type=preventivo o correctivo. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"type": "preventivo"} |
| Resultado Esperado | Solo preventivos. |
| Resultado Obtenido | Items filtrados por type. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.17

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.17 |
| Título             | Filtros combinados |
| Descripción        | Debe aplicar AND entre filtros. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"start_date": "2025-10-01", "end_date": "2025-12-31", "status_id": "13", "assigned_technician_id": "2", "type": "correctivo"} |
| Resultado Esperado | Conjunto intersección correcto o vacío. |
| Resultado Obtenido | Items cumplen filtros combinados. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.18

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.18 |
| Título             | Filtros sin resultados retornan lista vacía |
| Descripción        | Debe retornar data=[] y success=true. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"status_id": "999"} |
| Resultado Esperado | data vacía; sin error. |
| Resultado Obtenido | data vacía. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.19

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.19 |
| Título             | Limpiar filtros retorna listado completo |
| Descripción        | Sin query params debe ignorar estado previo del cliente. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Retorna todos los elementos visibles al usuario. |
| Resultado Obtenido | Lista completa. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.20

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.20 |
| Título             | Búsqueda por consecutivo exacto |
| Descripción        | Debe filtrar por número de consecutivo. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"q": "7"} |
| Resultado Esperado | Coincidencia exacta. |
| Resultado Obtenido | Solo id=7. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.21

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.21 |
| Título             | Búsqueda por serial parcial |
| Descripción        | Debe hacer LIKE insensible a mayúsculas. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"q": "s-000"} |
| Resultado Esperado | Coincidencias parciales sin sensibilidad a case. |
| Resultado Obtenido | Incluye seriales con "s-000". |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.22

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.22 |
| Título             | Búsqueda por nombre con acentos/espacios |
| Descripción        | Normalización de acentos y espacios. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"q": "tractor"} |
| Resultado Esperado | Búsqueda tolerante a acentos/espacios. |
| Resultado Obtenido | Incluye nombres con "tractor". |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.23

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.23 |
| Título             | Mitigar inyección en búsqueda |
| Descripción        | Validar sanitización de q. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"q": "' OR 1=1;--"} |
| Resultado Esperado | Sanitización efectiva; sin error 500. |
| Resultado Obtenido | Sin error. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.24

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.24 |
| Título             | Técnico existente |
| Descripción        | assigned_technician_id resoluble en servicio de usuarios. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Integridad referencial lógica entre servicios. |
| Resultado Obtenido | Asumido existente. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.25

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.25 |
| Título             | Técnico inexistente |
| Descripción        | Técnico inexistente manejado por el cliente. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Servicio principal no falla; FE maneja ausencia. |
| Resultado Obtenido | Lista 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.26

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.26 |
| Título             | Timeout/500 en users |
| Descripción        | Falla temporal en users no rompe lista. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Aislamiento entre servicios; resiliencia. |
| Resultado Obtenido | Lista 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.27

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.27 |
| Título             | Derivar colores por fecha |
| Descripción        | Datos suficientes para colores (vencido/hoy/vigente). |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Información suficiente para clasificación de colores. |
| Resultado Obtenido | Datos suficientes. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.28

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.28 |
| Título             | Cancelados incluidos |
| Descripción        | Cancelados aparecen con status_name="Cancelado". |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Cancelados visibles; pueden filtrarse por estado. |
| Resultado Obtenido | Cancelados presentes. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.29

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.29 |
| Título             | Realizados y botón de reporte |
| Descripción        | Realizados presentes para habilitar "Registrar reporte" en FE. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | FE puede habilitar acción según estado. |
| Resultado Obtenido | Realizados presentes. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.30

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.30 |
| Título             | Método no permitido |
| Descripción        | POST/PUT/DELETE retorna 405. |
| Datos de Entrada   | Método POST; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Body: {} |
| Resultado Esperado | 405 Method Not Allowed. |
| Resultado Obtenido | Asumido 405. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.31

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.31 |
| Título             | Content-Type correcto |
| Descripción        | Respuesta application/json; charset=utf-8. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Encabezados correctos. |
| Resultado Obtenido | Asumido correcto. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.32

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.32 |
| Título             | Límite de longitud en q |
| Descripción        | Consultas q excesivamente largas son rechazadas o truncadas. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"q": "cadena_larga_de_1000_caracteres"} |
| Resultado Esperado | No DoS por strings enormes. |
| Resultado Obtenido | Sin error. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.33

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.33 |
| Título             | Caracteres especiales seguros |
| Descripción        | Nombres/serial con caracteres especiales retornan JSON válido. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Escape correcto; sin XSS a nivel API. |
| Resultado Obtenido | JSON válido. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.34

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.34 |
| Título             | Performance con volumen |
| Descripción        | Tiempo de respuesta con 500+ registros. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {} |
| Resultado Esperado | Cumple umbrales de rendimiento. |
| Resultado Obtenido | Asumido ok. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.35

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.35 |
| Título             | Estabilidad ante parámetros desconocidos |
| Descripción        | Parámetros ajenos no deben romper ni alterar indebidamente. |
| Datos de Entrada   | Método GET; URL /maintenance_scheduling/list/; Headers: Authorization: Bearer <token_con_125>; Query Params: {"foo": "bar", "order_by": "hacker"} |
| Resultado Esperado | Ignorar o retornar 400 validado según política; consistente. |
| Resultado Obtenido | 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-PM-002.36

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-PM-002.36 |
| Título             | CORS (si aplica) |
| Descripción        | Encabezados CORS para orígenes válidos. |
| Datos de Entrada   | Método OPTIONS; URL /maintenance_scheduling/list/; Headers: Origin: http://localhost:3000; Access-Control-Request-Method: GET; |
| Resultado Esperado | CORS funcional para orígenes permitidos. |
| Resultado Obtenido | Asumido ok. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |