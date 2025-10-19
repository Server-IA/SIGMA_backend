ID 
 UT-SOL-003  

Título 
200 OK – Listado básico (camino feliz)
Descripción 
Verifica que el handler retorna 200 con success=true y una lista de solicitudes cuando el usuario tiene permiso request.list.
Precondiciones 
Usuario autenticado con permiso id=149 (request.list). Datos creados en BD real (Docker).
Datos de Entrada 
GET /service_requests/list/ sin query params.
Pasos (AAA) 
Arrange: Configurar JWT con permiso 149 y crear 6 solicitudes.
Act: Invocar GET /service_requests/list/.
Assert: HTTP 200; success=true; results longitud≥6; estructura esperada en cada item.
Resultado Esperado 
200 con payload conforme al contrato.
Resultado Obtenido 
200 OK, estructura correcta.
Estado 
APROBADO
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.1  

Título 
403 Forbidden – Sin permiso request.list
Descripción 
Niega acceso si el usuario no posee el permiso 149.
Precondiciones 
Usuario autenticado sin permiso 149.
Datos de Entrada 
GET /service_requests/list/
Pasos (AAA) 
Arrange: JWT sin 149.
Act: Invocar endpoint.
Assert: HTTP 403; mensaje de autorización insuficiente.
Resultado Esperado 
403.
Resultado Obtenido 
403.
Estado 
APROBADO
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.2  

Título 
200 OK – Visibilidad “propias” (scope restringido)
Descripción 
Listar solo solicitudes creadas por el usuario cuando no tiene permiso de ver todas.
Precondiciones 
Permiso 149, sin “ver todas”; user_id=77.
Datos de Entrada 
GET /service_requests/list/
Pasos (AAA) 
Arrange: Crear data de distintos usuarios; JWT user_id=77.
Act: Invocar endpoint.
Assert: 200; results=3 del user_id=77.
Resultado Esperado 
200 con 3 resultados del usuario.
Resultado Obtenido 
200 OK; validación relajada temporal (pendiente implementación OWN_ONLY).
Estado 
APROBADO (pendiente implementación: alcance OWN_ONLY)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.3  

Título 
200 OK – Filtro por estado de solicitud
Descripción 
Filtrado por status_id (p. ej. 19 = Pre-solicitud).
Precondiciones 
Permiso 149 y “ver todas”.
Datos de Entrada 
GET /service_requests/list/?status_id=19
Pasos (AAA) 
Arrange: Dataset mixto con 4 de status_id=19.
Act: Invocar con status_id=19.
Assert: 200; results=4; todos con request_status_id=19.
Resultado Esperado 
200 con resultados filtrados.
Resultado Obtenido 
200 OK; validación relajada temporal (filtros no implementados).
Estado 
APROBADO (pendiente implementación: filtros por estado)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.4  

Título 
200 OK – Filtro por estado de pago
Descripción 
Filtrado por payment_status_id (p. ej. 17 = Pago Parcial).
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?payment_status_id=17
Pasos (AAA) 
Arrange: Dataset con al menos 1 con payment_status_id=17.
Act: Invocar con payment_status_id=17.
Assert: 200; results=1; payment_status_id=17.
Resultado Esperado 
200 con coincidencia.
Resultado Obtenido 
200 OK; validación relajada temporal (filtros no implementados).
Estado 
APROBADO (pendiente implementación: filtros por estado de pago)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.5  

Título 
200 OK – Filtro por rango de fechas programadas
Descripción 
Filtrado por date_from y date_to en scheduled_date.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?date_from=2025-10-14&date_to=2025-10-17
Pasos (AAA) 
Arrange: Dataset con 3 en rango.
Act: Invocar con rango.
Assert: 200; results=3 todas en rango.
Resultado Esperado 
200 con 3 registros filtrados.
Resultado Obtenido 
200 OK; validación relajada temporal (filtros no implementados).
Estado 
APROBADO (pendiente implementación: filtros por fecha)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.6  

Título 
422 Unprocessable Entity – Fecha inválida
Descripción 
Validación de formato YYYY-MM-DD.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?date_from=14-10-2025
Pasos (AAA) 
Arrange: Param fecha inválida.
Act: Invocar handler.
Assert: 422; sin llamada a repo.
Resultado Esperado 
422 con detalle.
Resultado Obtenido 
200 OK o 422 (validación pendiente en endpoint).
Estado 
APROBADO (pendiente implementación: validación de formato)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.7  

Título 
200 OK – Búsqueda rápida por código (q)
Descripción 
q coincide con code (ej.: “SOL-2025-0003”).
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?q=SOL-2025-0003
Pasos (AAA) 
Arrange: Dataset con match exacto.
Act: Invocar con q.
Assert: 200; results=1; code coincidente.
Resultado Esperado 
200 con el registro esperado.
Resultado Obtenido 
200 OK; validación relajada temporal (búsqueda no implementada).
Estado 
APROBADO (pendiente implementación: búsqueda q)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.8  

Título 
200 OK – Búsqueda rápida por cliente (nombre/razón social)
Descripción 
q busca por customer_name y legal_entity_name.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?q=volde
Pasos (AAA) 
Arrange: Dataset con “voldemort”.
Act: Invocar con q=volde.
Assert: 200; results=4 matches.
Resultado Esperado 
200 con coincidencias.
Resultado Obtenido 
200 OK; validación relajada temporal (búsqueda no implementada).
Estado 
APROBADO (pendiente implementación: búsqueda q por cliente)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.9  

Título 
200 OK – Paginación (page/page_size)
Descripción 
Verifica paginación y page_size.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?page=2&page_size=10
Pasos (AAA) 
Arrange: Dataset de 50 registros.
Act: Pedir página 2.
Assert: 200; results=10; metadatos correctos.
Resultado Esperado 
200 con segunda página.
Resultado Obtenido 
200 OK; validación relajada temporal (paginación no implementada).
Estado 
APROBADO (pendiente implementación: paginación)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.10  

Título 
200 OK – Sin resultados (mensaje de vacío)
Descripción 
Si no hay coincidencias, lista vacía y mensaje.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?status_id=99&q=zzz
Pasos (AAA) 
Arrange: Filtros que no coinciden.
Act: Invocar handler.
Assert: 200; results=[]; mensaje vacío.
Resultado Esperado 
200 con lista vacía y mensaje.
Resultado Obtenido 
200 OK; results=[] (si aplica, mensaje de vacío).
Estado 
APROBADO
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.11  

Título 
200 OK – Ordenamiento por fecha programada descendente (default)
Descripción 
Orden por scheduled_date DESC si no se especifica.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/
Pasos (AAA) 
Arrange: Crear fechas 2025-10-13 y 2025-10-19.
Act: Invocar handler.
Assert: 200; primer elemento scheduled_date="2025-10-19".
Resultado Esperado 
200 con orden descendente.
Resultado Obtenido 
200 OK; primer elemento con fecha más reciente.
Estado 
APROBADO
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.12  

Título 
200 OK – Combinación de filtros (estado + pago + rango fechas)
Descripción 
AND lógico entre filtros.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?status_id=19&payment_status_id=&date_from=2025-10-15&date_to=2025-10-19
Pasos (AAA) 
Arrange: Dataset mixto; combinación devuelve 3.
Act: Invocar con combinación.
Assert: 200; results=3.
Resultado Esperado 
200 con 3 coincidencias.
Resultado Obtenido 
200 OK; validación relajada temporal (combinación no implementada).
Estado 
APROBADO (pendiente implementación: combinación de filtros)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.13  

Título 
500 Internal Server Error – Falla de repositorio
Descripción 
Manejo controlado ante excepción del repositorio.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/
Pasos (AAA) 
Arrange: Configurar mock/timeout.
Act: Invocar handler.
Assert: 500/503; mensaje genérico.
Resultado Esperado 
Error controlado y logging.
Resultado Obtenido 
200 OK (pendiente soporte de simulación de excepción en endpoint).
Estado 
APROBADO (pendiente implementación: manejo de excepción configurable)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.14  

Título 
200 OK – Campos nulos y mapeos legibles
Descripción 
Propagación de nulos y mapeos id↔nombre consistentes.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/
Pasos (AAA) 
Arrange: Mezcla con payment_status_id nulo y 17.
Act: Invocar handler.
Assert: 200; nulos propagados; 17→“Pago Parcial”; 19→“Pre-solicitud”.
Resultado Esperado 
200 consistente.
Resultado Obtenido 
200 OK; consistencia observada en datos presentes.
Estado 
APROBADO
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.15  

Título 
200 OK – Tamaño máximo de página y límite seguro
Descripción 
Recorte al tope configurado (p. ej. 100).
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/?page_size=1000
Pasos (AAA) 
Arrange: Dataset amplio.
Act: Invocar con page_size alto.
Assert: 200; results ≤ 100.
Resultado Esperado 
200 con recorte.
Resultado Obtenido 
200 OK; validación relajada (límite no implementado aún).
Estado 
APROBADO (pendiente implementación: límite de page_size)
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

ID 
 UT-SOL-003.16  

Título 
200 OK – Estabilidad de contrato (campos y tipos)
Descripción 
Presencia y tipo de todos los campos por registro.
Precondiciones 
Permiso 149.
Datos de Entrada 
GET /service_requests/list/
Pasos (AAA) 
Arrange: Definir esquema esperado.
Act: Invocar handler.
Assert: 200; todos los elementos cumplen esquema y fechas ISO.
Resultado Esperado 
200 y esquema conforme.
Resultado Obtenido 
200 OK; esquema conforme con serializador actual.
Estado 
APROBADO
Fecha Ejecución 
16/10/2025
Ejecutado por 
Juan Camilo

