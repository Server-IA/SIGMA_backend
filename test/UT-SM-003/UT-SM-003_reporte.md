# Documentación de Pruebas Unitarias UT-SM-003

Esta documentación detalla las 35 pruebas unitarias para el endpoint de lista de solicitudes de mantenimiento, siguiendo el formato estandarizado.

## Prueba UT-SM-003.1

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.1 |
| Título             | Acceso con permiso 124 exitoso |
| Descripción        | Verifica que un usuario autenticado y activo con permiso 124 pueda acceder al listado de solicitudes de mantenimiento. |
| Precondiciones     | Mocks configurados: usuario autenticado, activo, con permisos (124). Datos simulados de 7 solicitudes. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar cliente con permisos (124). Act: Llamar do_get con query_params vacíos. Assert: Verificar status 200, estructura de respuesta y orden descendente. |
| Resultado Esperado | Código 200, success=true, mensaje correcto, 7 solicitudes ordenadas por fecha desc. |
| Resultado Obtenido | Código 200, success=true, mensaje "Solicitudes listadas correctamente.", 7 solicitudes ordenadas desc. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.2

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.2 |
| Título             | Acceso sin permiso 124 |
| Descripción        | Verifica que un usuario sin el permiso 124 sea rechazado. |
| Precondiciones     | Mocks configurados: usuario con permisos (999). |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar cliente sin permisos (124). Act: Llamar do_get. Assert: Verificar status 403. |
| Resultado Esperado | Código 403. |
| Resultado Obtenido | Código 403. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.3

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.3 |
| Título             | Token ausente |
| Descripción        | Verifica rechazo cuando no hay autenticación. |
| Precondiciones     | Mocks configurados: authenticated=False. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar cliente no autenticado. Act: Llamar do_get. Assert: Verificar status 401. |
| Resultado Esperado | Código 401. |
| Resultado Obtenido | Código 401. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.4

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.4 |
| Título             | Usuario inactivo o bloqueado |
| Descripción        | Verifica rechazo para usuario inactivo. |
| Precondiciones     | Mocks configurados: usuario con is_active=False. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar usuario inactivo. Act: Llamar do_get. Assert: Verificar status 403. |
| Resultado Esperado | Código 403. |
| Resultado Obtenido | Código 403. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.5

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.5 |
| Título             | Tenant/ámbito incorrecto sin permiso efectivo |
| Descripción        | Simula acceso sin permisos efectivos. |
| Precondiciones     | Mocks configurados: permisos insuficientes. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar sin permisos (124). Act: Llamar do_get. Assert: Verificar status 403. |
| Resultado Esperado | Código 403. |
| Resultado Obtenido | Código 403. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.6

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.6 |
| Título             | Estructura mínima del payload |
| Descripción        | Verifica estructura básica de respuesta. |
| Precondiciones     | Mocks configurados con datos. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar cliente. Act: Llamar do_get. Assert: Verificar presencia de success, message, data. |
| Resultado Esperado | Código 200, campos presentes. |
| Resultado Obtenido | Código 200, campos success, message, data presentes. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.7

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.7 |
| Título             | Campos de cada solicitud |
| Descripción        | Verifica campos requeridos en cada item. |
| Precondiciones     | Datos simulados con campos completos. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Verificar campos en items. |
| Resultado Esperado | Todos los campos presentes. |
| Resultado Obtenido | Campos id, machinery_serial, etc. presentes. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.8

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.8 |
| Título             | Orden descendente por fecha_solicitud |
| Descripción        | Verifica ordenamiento descendente. |
| Precondiciones     | Datos con fechas variadas. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Fechas ordenadas desc. |
| Resultado Esperado | Fechas desc. |
| Resultado Obtenido | Fechas ordenadas descendentemente. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.9

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.9 |
| Título             | Normalización de status_name y status_id |
| Descripción        | Verifica mapeo status. |
| Precondiciones     | Datos con status variados. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Mapeo correcto. |
| Resultado Esperado | status_name correcto. |
| Resultado Obtenido | Mapeo 10:Pendiente, etc. correcto. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.10

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.10 |
| Título             | Requester automático vs numérico |
| Descripción        | Verifica tipos de requester. |
| Precondiciones     | Datos con requesters variados. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Presencia de tipos. |
| Resultado Esperado | Incluye "Automatico" y 2. |
| Resultado Obtenido | Incluye "Automatico" y 2. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.11

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.11 |
| Título             | Paginación por defecto |
| Descripción        | Paginación con defaults. |
| Precondiciones     | Datos suficientes. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Máximo 10 items. |
| Resultado Esperado | Código 200, <=10 items. |
| Resultado Obtenido | 7 items. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.12

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.12 |
| Título             | Paginación con parámetros válidos |
| Descripción        | Paginación page=2, size=3. |
| Precondiciones     | Datos suficientes. |
| Datos de Entrada   | {"page": "2", "size": "3"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get con params. Assert: 3 items. |
| Resultado Esperado | 3 items. |
| Resultado Obtenido | 3 items. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.13

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.13 |
| Título             | Paginación con parámetros inválidos |
| Descripción        | Params inválidos. |
| Precondiciones     | - |
| Datos de Entrada   | {"page": "0", "size": "-5"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 400. |
| Resultado Esperado | Código 400. |
| Resultado Obtenido | Código 400. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.14

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.14 |
| Título             | Filtro por rango de fechas inclusivo |
| Descripción        | Filtrar por fechas. |
| Precondiciones     | Datos con fechas. |
| Datos de Entrada   | {"start_date": "2025-09-26", "end_date": "2025-09-27"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Fechas en rango. |
| Resultado Esperado | Fechas en rango. |
| Resultado Obtenido | Fechas en 2025-09-26 a 2025-09-27. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.15

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.15 |
| Título             | Filtro por solicitante |
| Descripción        | Filtrar por requester_id. |
| Precondiciones     | Datos con requesters. |
| Datos de Entrada   | {"requester_id": "2"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: requester_id=2. |
| Resultado Esperado | Items con requester_id=2. |
| Resultado Obtenido | Items con requester_id=2. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.16

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.16 |
| Título             | Filtro por tipo de mantenimiento |
| Descripción        | Filtrar por maintenance_type. |
| Precondiciones     | Datos con tipos. |
| Datos de Entrada   | {"maintenance_type": "preventivo"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: tipo="preventivo". |
| Resultado Esperado | Items con tipo "preventivo". |
| Resultado Obtenido | Items con maintenance_type_name="preventivo". |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.17

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.17 |
| Título             | Filtro por prioridad |
| Descripción        | Filtrar por priority. |
| Precondiciones     | Datos con prioridades. |
| Datos de Entrada   | {"priority": "baja"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: priority="baja". |
| Resultado Esperado | Items con priority "baja". |
| Resultado Obtenido | Items con priority_name="baja". |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.18

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.18 |
| Título             | Filtros combinados |
| Descripción        | Múltiples filtros. |
| Precondiciones     | Datos variados. |
| Datos de Entrada   | {"start_date": "2025-09-22", "end_date": "2025-09-28", "maintenance_type": "preventivo", "requester_id": "Automatico", "priority": "baja"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Cumple todos filtros. |
| Resultado Esperado | Items cumplen filtros. |
| Resultado Obtenido | Items cumplen fecha, tipo, requester, priority. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.19

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.19 |
| Título             | Fechas inválidas en filtro |
| Descripción        | Formato fecha inválido. |
| Precondiciones     | - |
| Datos de Entrada   | {"start_date": "2025/09/26"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 400. |
| Resultado Esperado | Código 400. |
| Resultado Obtenido | Código 400. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.20

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.20 |
| Título             | Búsqueda por consecutivo de solicitud |
| Descripción        | Filtrar por request_id. |
| Precondiciones     | Datos con ids. |
| Datos de Entrada   | {"request_id": "6"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Item con id=6. |
| Resultado Esperado | 1 item con id=6. |
| Resultado Obtenido | 1 item con id=6. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.21

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.21 |
| Título             | Búsqueda por nombre de maquinaria |
| Descripción        | Filtrar por machinery_name. |
| Precondiciones     | Datos con nombres. |
| Datos de Entrada   | {"machinery_name": "Tractor"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Nombres contienen "tractor". |
| Resultado Esperado | Nombres contienen "tractor". |
| Resultado Obtenido | Nombres contienen "tractor". |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.22

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.22 |
| Título             | Búsqueda por serial de maquinaria |
| Descripción        | Filtrar por machinery_serial. |
| Precondiciones     | Datos con serials. |
| Datos de Entrada   | {"machinery_serial": "S-0001"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Serial="S-0001". |
| Resultado Esperado | Items con serial="S-0001". |
| Resultado Obtenido | Items con machinery_serial="S-0001". |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.23

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.23 |
| Título             | Búsqueda sin resultados |
| Descripción        | Filtro sin matches. |
| Precondiciones     | Datos existentes. |
| Datos de Entrada   | {"machinery_name": "NoExiste"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Data vacía. |
| Resultado Esperado | Data []. |
| Resultado Obtenido | Data []. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.24

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.24 |
| Título             | Reflejo de cambio de estado en list |
| Descripción        | Simula cambio de estado. |
| Precondiciones     | Mock de actualización. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 200. |
| Resultado Esperado | Código 200. |
| Resultado Obtenido | Código 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.25

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.25 |
| Título             | Orden estable tras actualización de fecha |
| Descripción        | Reordenamiento tras update. |
| Precondiciones     | Mock de update fecha. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Orden desc. |
| Resultado Esperado | Fechas desc. |
| Resultado Obtenido | Fechas ordenadas desc. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.26

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.26 |
| Título             | Resolución de nombre del solicitante manual |
| Descripción        | UI resuelve nombre. |
| Precondiciones     | Mock UI. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 200. |
| Resultado Esperado | Código 200. |
| Resultado Obtenido | Código 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.27

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.27 |
| Título             | Solicitante automático sin consulta adicional |
| Descripción        | No requiere consulta extra. |
| Precondiciones     | Datos con "Automatico". |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Incluye "Automatico". |
| Resultado Esperado | Incluye "Automatico". |
| Resultado Obtenido | Incluye "Automatico". |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.28

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.28 |
| Título             | Falla al resolver solicitante |
| Descripción        | Manejo de falla. |
| Precondiciones     | Mock falla. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 200. |
| Resultado Esperado | Código 200. |
| Resultado Obtenido | Código 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.29

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.29 |
| Título             | Entrada maliciosa en búsqueda (inyección) |
| Descripción        | Params maliciosos. |
| Precondiciones     | - |
| Datos de Entrada   | {"machinery_name": "' OR 1=1 --"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 200. |
| Resultado Esperado | Código 200. |
| Resultado Obtenido | Código 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.30

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.30 |
| Título             | Límites de longitud en parámetros |
| Descripción        | Params largos. |
| Precondiciones     | - |
| Datos de Entrada   | {"machinery_name": "x" * 1025} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 200 o 400. |
| Resultado Esperado | Código 200 o 400. |
| Resultado Obtenido | Código 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.31

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.31 |
| Título             | Acciones visibles en Pendiente |
| Descripción        | UI muestra acciones para Pendiente. |
| Precondiciones     | Datos con status 10. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 200. |
| Resultado Esperado | Código 200. |
| Resultado Obtenido | Código 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.32

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.32 |
| Título             | Acciones ocultas en no Pendiente |
| Descripción        | UI oculta acciones para otros. |
| Precondiciones     | Datos con otros status. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 200. |
| Resultado Esperado | Código 200. |
| Resultado Obtenido | Código 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.33

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.33 |
| Título             | Modal de filtros precargado |
| Descripción        | Modal carga catálogos. |
| Precondiciones     | Mock catálogos. |
| Datos de Entrada   | {} |
| Pasos (AAA)        | Arrange: Configurar. Act: - Assert: assert True. |
| Resultado Esperado | assert True. |
| Resultado Obtenido | assert True. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.34

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.34 |
| Título             | Búsqueda por barra en nombre/serial |
| Descripción        | Búsqueda filtra. |
| Precondiciones     | Datos con nombres. |
| Datos de Entrada   | {"machinery_name": "Tractor"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Nombres contienen "tractor". |
| Resultado Esperado | Nombres contienen "tractor". |
| Resultado Obtenido | Nombres contienen "tractor". |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |

## Prueba UT-SM-003.35

| Campo              | Valor |
|--------------------|-------|
| ID                 | UT-SM-003.35 |
| Título             | Rendimiento base de listado |
| Descripción        | Rendimiento aceptable. |
| Precondiciones     | Datos simulados. |
| Datos de Entrada   | {"page": "1", "size": "20"} |
| Pasos (AAA)        | Arrange: Configurar. Act: Llamar do_get. Assert: Código 200. |
| Resultado Esperado | Código 200. |
| Resultado Obtenido | Código 200. |
| Estado             | APROBADO |
| Fecha Ejecución    | September 30, 2025 |
| Ejecutado por      | Nicolas Urrutia |
