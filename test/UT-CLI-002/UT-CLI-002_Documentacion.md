# Documentación de Pruebas UT-CLI-002

**Historia de Usuario:** HU-CLI-002 - Listar Clientes con Filtros y Paginación  
**Endpoints Probados:**
- `GET /customers/`
- `GET /customers/active/`

**Ejecutado por:** Nicolas Urrutia  
**Fecha de Ejecución:** 11 de Octubre, 2025  
**Entorno:** Docker (Django + PostgreSQL + pytest)  
**Resultado Global:** ✅ **11/11 pruebas ejecutadas APROBADAS (100%)**  
**Funcionalidades No Implementadas:** 15 casos marcados como SKIPPED

---

## Prueba UT-CLI-002.1

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.1 |
| **Título** | Listado básico de clientes OK |
| **Descripción** | Verifica que GET /customers/ responde 200 con success=true y un arreglo data de clientes con los campos principales requeridos por el listado HU-CLI-002. |
| **Precondiciones** | Usuario autenticado con permiso customer.list; base con al menos 3 clientes mixtos (persona natural y jurídica). |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{"Authorization":"Bearer <token_con_permiso_list>"}}` |
| **Pasos (AAA)** | Arrange: Cargar datos de clientes y autenticar usuario con permiso customer.list. Act: Enviar GET /customers/ con token válido. Assert: Status 200; body con success=true y data como arreglo; cada item contiene id_customer, document_number, type_document_id/name, person_type_id/name, legal_entity_name o combinación de nombre y apellidos, email, phone, customer_statues_id/name. |
| **Resultado Esperado** | Respuesta 200 con estructura JSON válida y campos presentes para renderizar columnas solicitadas. |
| **Resultado Obtenido** | Status 200, success=true, data con 3 clientes incluyendo todos los campos requeridos. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.2

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.2 |
| **Título** | Acceso sin token retorna 401 |
| **Descripción** | Verifica que acceder a /customers/ sin Authorization header retorna 401 Unauthorized al requerir autenticación. |
| **Precondiciones** | Ninguna; petición sin token. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{}}` |
| **Pasos (AAA)** | Arrange: No configurar token. Act: Enviar GET /customers/ sin Authorization. Assert: Status 401; mensaje de autenticación requerida; sin datos sensibles. |
| **Resultado Esperado** | 401 Unauthorized cuando faltan credenciales válidas. |
| **Resultado Obtenido** | Status 401, mensaje "Authentication credentials were not provided."; sin exposición de datos. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.3

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.3 |
| **Título** | Sin permiso customer.list retorna 403 |
| **Descripción** | Verifica que un usuario autenticado sin permiso customer.list recibe 403 Forbidden al carecer de autorización para listar clientes. |
| **Precondiciones** | Usuario autenticado sin permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{"Authorization":"Bearer <token_sin_permiso_list>"}}` |
| **Pasos (AAA)** | Arrange: Autenticar cuenta sin permiso requerido. Act: GET /customers/. Assert: Status 403; mensaje indicando falta de permisos. |
| **Resultado Esperado** | 403 Forbidden para usuario autenticado sin permisos de consulta. |
| **Resultado Obtenido** | Status 403, mensaje "No tiene permisos para listar clientes."; sin acceso a datos. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.4

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.4 |
| **Título** | Estructura mínima y tipos en /customers/ |
| **Descripción** | Valida que success sea boolean, data sea arreglo y cada campo tenga tipo consistente (ej. id_customer número, email string, phone string o null). |
| **Precondiciones** | Usuario con customer.list; base con datos variados. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Preparar dataset con nulos y valores completos. Act: GET /customers/. Assert: Validar tipos JSON según contrato y que null sea usado donde aplique. |
| **Resultado Esperado** | JSON válido con tipados coherentes y sin violar gramática JSON. |
| **Resultado Obtenido** | success es boolean, data es array; id_customer es int, type_document_name es string/null, customer_statues_name es string; tipos coherentes. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.5

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.5 |
| **Título** | Paginación page y pageSize |
| **Descripción** | Verifica soporte de paginación con parámetros page y pageSize y presencia de metadatos (total, page, pageSize, hasNext/links). |
| **Precondiciones** | 50+ clientes en base; usuario con customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?page=2&pageSize=20","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Insertar 50 clientes. Act: GET con page=2&pageSize=20. Assert: 200; data.length=20; metadatos presentes y coherentes. |
| **Resultado Esperado** | Paginación estándar con metadatos y navegabilidad clara. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Funcionalidad de paginación no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.6

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.6 |
| **Título** | Paginación limit y offset |
| **Descripción** | Si la API usa limit/offset, verifica que GET /customers/?limit=25&offset=25 devuelva 25 registros y, si existen, enlaces a next/prev. |
| **Precondiciones** | 60+ clientes; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?limit=25&offset=25","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Población de datos suficiente. Act: GET con limit/offset. Assert: 200; conteos correctos; offsets consistentes. |
| **Resultado Esperado** | Soporte consistente de limit/offset si está implementado. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Paginación limit/offset no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.7

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.7 |
| **Título** | Paginación con parámetros inválidos |
| **Descripción** | Valida manejo de page/pageSize negativos, cero o no numéricos retornando 400 o normalizando valores por defecto. |
| **Precondiciones** | Usuario con customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?page=-1&pageSize=abc","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Preparar petición inválida. Act: GET con parámetros inválidos. Assert: 400 con detalle de validación o fallback a defaults documentados. |
| **Resultado Esperado** | Validación robusta de parámetros de paginación. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Validación de parámetros de paginación no disponible. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.8

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.8 |
| **Título** | Filtro por nombre o razón social |
| **Descripción** | Verifica que /customers/ acepte filtro por nombre/razón social y retorne coincidencias exactas o parciales según documentación. |
| **Precondiciones** | Datos con mezcla de name y legal_entity_name; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?name=Juan","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Cargar clientes con nombres coincidentes y no coincidentes. Act: GET con name=Juan. Assert: 200; solo clientes coincidentes incluidos; no falsos positivos. |
| **Resultado Esperado** | Filtro efectivo y determinista por nombre/razón social. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Filtro por nombre no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.9

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.9 |
| **Título** | Filtro por tipo de identificación |
| **Descripción** | Verifica filtro por type_document_id para restringir por tipo de documento. |
| **Precondiciones** | Datos con distintos type_document_id; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?type_document_id=1","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Población con varios tipos. Act: GET con type_document_id=1. Assert: 200; solo registros con type_document_id=1. |
| **Resultado Esperado** | Resultados filtrados correctamente por tipo de documento. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Filtro por tipo de documento no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.10

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.10 |
| **Título** | Filtro por documento de identificación |
| **Descripción** | Verifica filtro por document_number exacto y por prefijo cuando se permita búsqueda parcial. |
| **Precondiciones** | Datos con document_number repetidos y únicos; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?document_number=1079172264","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Insertar registros con números similares. Act: GET con document_number exacto. Assert: 200; coincidencias exactas retornadas; no incluir otros. |
| **Resultado Esperado** | Coincidencia precisa por documento según parámetro. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Filtro por document_number no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.11

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.11 |
| **Título** | Filtro por estado del cliente |
| **Descripción** | Verifica que el filtro status devuelva clientes Activo/Inactivo según customer_statues_id/name. |
| **Precondiciones** | Clientes con estados variados; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?status=Activo","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Preparar estados Activo e Inactivo. Act: GET con status=Activo. Assert: 200; solo Activo; ninguno Inactivo. |
| **Resultado Esperado** | Filtrado correcto por estado del cliente. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Filtro por status no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.12

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.12 |
| **Título** | Filtro por teléfono o email |
| **Descripción** | Verifica filtro por phone y por email, aceptando coincidencias exactas o parciales según documentación. |
| **Precondiciones** | Datos con phones y emails distintos; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?email=juan%40gmail.com","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Cargar registros con emails/phones variados. Act: GET con email=... Assert: 200; resultados coincidentes; case-insensitive cuando aplique. |
| **Resultado Esperado** | Filtrado funcional por email/teléfono. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Filtro por email/phone no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.13

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.13 |
| **Título** | Combinación de filtros (AND) |
| **Descripción** | Verifica que múltiples filtros se apliquen con lógica AND y restrinjan correctamente el conjunto. |
| **Precondiciones** | Datos con combinaciones que cumplan y no cumplan; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?status=Activo&type_document_id=1&name=Juan","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Sembrar datos para casos positivos y negativos. Act: GET con filtros AND. Assert: 200; solo registros que cumplen todos los filtros. |
| **Resultado Esperado** | Composición AND de filtros coherente y documentada. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Filtros combinados no disponibles en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.14

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.14 |
| **Título** | Búsqueda rápida por nombre/documento |
| **Descripción** | Verifica parámetro de búsqueda rápida (p. ej., q o search) que busque por nombre/razón social o documento. |
| **Precondiciones** | Datos con coincidencias parciales; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?q=10791722","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Incluir registros que contengan el token de búsqueda. Act: GET con q=... Assert: 200; incluye coincidencias por documento o nombre según alcance. |
| **Resultado Esperado** | Búsqueda rápida funcional en campos clave. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Búsqueda rápida no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.15

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.15 |
| **Título** | Sin resultados muestra lista vacía |
| **Descripción** | Verifica que al no haber coincidencias la API retorna success=true con data=[], permitiendo al cliente mostrar el mensaje "No se encontraron clientes...". |
| **Precondiciones** | Filtros que no coinciden con ningún registro; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?name=ZZZ_NoExiste","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Asegurar inexistencia de coincidencias. Act: GET con filtro imposible. Assert: 200; data=[]; sin errores. |
| **Resultado Esperado** | Lista vacía sin error para que el frontend muestre el mensaje. |
| **Resultado Obtenido** | Status 200, success=true, data=[]; sin errores. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.16

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.16 |
| **Título** | Codificación UTF-8 en nombres y tipos |
| **Descripción** | Verifica que strings con acentos (Cédula de Ciudadanía, Persona Jurídica) se entreguen y decodifiquen correctamente en UTF-8 conforme RFC 8259. |
| **Precondiciones** | Registros con valores acentuados en type_document_name y person_type_name. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Insertar valores con acentos y caracteres Unicode. Act: GET /customers/. Assert: 200; sin caracteres "mojibake"; válido UTF-8 por especificación JSON. |
| **Resultado Esperado** | Cadenas Unicode correctas sin corrupción de caracteres. |
| **Resultado Obtenido** | Status 200, caracteres UTF-8 correctos: "José", "María", "Ñoño", "Cédula de Ciudadanía"; sin corrupción. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.17

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.17 |
| **Título** | Usuario Activo: derivación Sí/No |
| **Descripción** | Verifica que la API exponga o permita derivar "Usuario Activo (Sí/No)" por asociación a cuenta id_user con estado activo; si no existe el campo, validar presencia de id_user para habilitar validación posterior. |
| **Precondiciones** | Clientes con id_user activo, id_user inactivo y id_user null. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Configurar usuarios con is_active true/false y clientes asociados. Act: GET /customers/. Assert: 200; si existe user_active, validar true/false; si no, validar id_user null->No y id_user!=null requiere verificación adicional. |
| **Resultado Esperado** | Información suficiente para mostrar "Usuario Activo (Sí/No)" conforme criterio funcional. |
| **Resultado Obtenido** | Status 200, campo id_user presente en respuesta; clientes con id_user=1 y clientes con id_user=null correctamente diferenciados. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.18

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.18 |
| **Título** | Actualización inmediata tras crear cliente |
| **Descripción** | Verifica consistencia de lectura: luego de crear un cliente, GET /customers/ refleja el nuevo registro inmediatamente (real-time a nivel de consulta). |
| **Precondiciones** | Endpoint de creación funcional; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Crear cliente nuevo vía POST. Act: GET inmediatamente después. Assert: 200; data incluye el nuevo cliente sin retrasos visibles. |
| **Resultado Esperado** | Lectura coherente post-escritura sin necesidad de recarga manual. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Requiere configuración completa del endpoint create_customer con permisos y auditoría. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.19

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.19 |
| **Título** | Actualización inmediata tras cambiar estado |
| **Descripción** | Cambiar estado de un cliente a Inactivo y verificar en GET /customers/ y GET /customers/active/ que el estado y pertenencia al listado activo cambian en tiempo real. |
| **Precondiciones** | Cliente en estado Activo existente; permisos correspondientes. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/active/","headers":{"Authorization":"Bearer <token_list_actives>"}}` |
| **Pasos (AAA)** | Arrange: Cambiar estado a Inactivo. Act: GET /customers/ y /customers/active/. Assert: 200; estado actualizado y cliente excluido de activos. |
| **Resultado Esperado** | Coherencia entre listados general y de activos tras el cambio. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Requiere implementación de toggle-status y verificación de listados. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.20

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.20 |
| **Título** | /customers/active/ solo incluye Activo |
| **Descripción** | Verifica que el endpoint de activos devuelva únicamente clientes con customer_statues_name/id que representen "Activo". |
| **Precondiciones** | Datos con Activo e Inactivo; permiso customer.list_activar. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/active/","headers":{"Authorization":"Bearer <token_actives>"}}` |
| **Pasos (AAA)** | Arrange: Asegurar mezcla de estados. Act: GET /customers/active/. Assert: 200; ningún Inactivo presente; todos Active. |
| **Resultado Esperado** | Lista estricta de clientes activos. |
| **Resultado Obtenido** | Status 200, solo clientes con customer_statues_name="Activo" y customer_statues_id=1; ningún cliente inactivo incluido. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.21

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.21 |
| **Título** | /customers/active/ sin permiso retorna 403 |
| **Descripción** | Verifica que el acceso a /customers/active/ por usuario autenticado sin permiso customer.list_activar retorna 403 Forbidden. |
| **Precondiciones** | Usuario autenticado sin permiso customer.list_activar. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/active/","headers":{"Authorization":"Bearer <token_sin_permiso_actives>"}}` |
| **Pasos (AAA)** | Arrange: Autenticar sin permiso. Act: GET /customers/active/. Assert: 403 con mensaje de autorización insuficiente. |
| **Resultado Esperado** | 403 Forbidden por falta de permiso específico. |
| **Resultado Obtenido** | Status 403, mensaje "No tiene permisos para listar clientes."; sin acceso a datos. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.22

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.22 |
| **Título** | Metadatos de paginación en respuesta |
| **Descripción** | Verifica presencia de objeto meta con total, page/pageSize o limit/offset, y enlaces de navegación en colecciones paginadas. |
| **Precondiciones** | 100+ clientes; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?page=1&pageSize=50","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Insertar 100 registros. Act: GET paginado. Assert: 200; meta presente y valores correctos; enlaces next/prev si aplican. |
| **Resultado Esperado** | Respuesta con contexto de paginación para UX eficiente. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Metadatos de paginación no disponibles en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.23

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.23 |
| **Título** | Manejo de nulos en phone y address |
| **Descripción** | Verifica que campos opcionales puedan ser null sin romper la serialización y que se mantenga consistencia de tipo string cuando no sean null. |
| **Precondiciones** | Registros con phone/address null y con valores. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Preparar variedad de datos. Act: GET /customers/. Assert: 200; null permitido; sin strings vacíos inesperados donde se espera null. |
| **Resultado Esperado** | Tolerancia a nulls en campos opcionales. |
| **Resultado Obtenido** | Status 200, campos phone y address pueden ser null o string; tipos coherentes; sin strings vacíos donde debería ser null. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.24

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.24 |
| **Título** | Ordenamiento por nombre ascendente |
| **Descripción** | Si existe parámetro sort, verifica sort=name&order=asc devuelve resultados ordenados alfabéticamente por Nombre o Razón Social. |
| **Precondiciones** | Datos con nombres variados; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?sort=name&order=asc","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Sembrar datos desordenados. Act: GET con sort=name&order=asc. Assert: 200; verificar orden lexicográfico. |
| **Resultado Esperado** | Orden estable y predecible al solicitar sort. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Ordenamiento no disponible en el endpoint actual. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba UT-CLI-002.25

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.25 |
| **Título** | Robustez ante inyección en filtros |
| **Descripción** | Valida que parámetros de filtro no permitan inyección (p. ej., name="Juan' OR '1'='1") y que la API responda de forma segura. |
| **Precondiciones** | Sistema con validación/parametrización de consultas; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/?name=Juan'%20OR%20'1'%3D'1","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Preparar consulta maliciosa. Act: GET con payload de inyección. Assert: 200 o 400 seguro; sin exposición de errores SQL; resultados no amplificados. |
| **Resultado Esperado** | Manejo seguro y saneado de parámetros de consulta. |
| **Resultado Obtenido** | NO IMPLEMENTADO - Requiere análisis de seguridad más profundo con filtros implementados. |
| **Estado** | NO APROBADO (SKIPPED) ⚠️ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Prueba ADICIONAL: Tiempo de respuesta

| Campo | Valor |
|-------|-------|
| **ID** | UT-CLI-002.26 |
| **Título** | Validación de tiempo de respuesta menor a 3 segundos |
| **Descripción** | Evalúa tiempos de respuesta al listar 50 clientes. |
| **Precondiciones** | 50 clientes en base; permiso customer.list. |
| **Datos de Entrada** | `{"method":"GET","path":"/customers/","headers":{"Authorization":"Bearer <token_list>"}}` |
| **Pasos (AAA)** | Arrange: Crear 50 clientes. Act: GET /customers/ midiendo tiempo. Assert: Tiempo de respuesta < 3 segundos; status 200. |
| **Resultado Esperado** | Respuesta en menos de 3 segundos. |
| **Resultado Obtenido** | Tiempo de respuesta: 0.002 segundos; Status 200. |
| **Estado** | APROBADO ✅ |
| **Fecha Ejecución** | Octubre 11, 2025 |
| **Ejecutado por** | Nicolas Urrutia |

---

## Resumen de Resultados

| Estado | Cantidad |
|--------|----------|
| APROBADO | 11 |
| NO APROBADO (SKIPPED - Funcionalidad no implementada) | 15 |
| **TOTAL** | **26** |

**Tasa de Aprobación (Pruebas Ejecutadas):** 100% (11/11)  
**Funcionalidades Pendientes de Implementación:** 15 casos

---

## Observaciones y Recomendaciones

1. **Funcionalidad Básica Correcta:** El endpoint GET /customers/ y GET /customers/active/ funcionan correctamente con:
   - Autenticación y autorización apropiadas
   - Estructura de datos coherente y tipados correctos
   - Manejo adecuado de valores nulos
   - Codificación UTF-8 correcta
   - Tiempos de respuesta excelentes

2. **Funcionalidades No Implementadas:** Las siguientes funcionalidades están pendientes de implementación:
   - **Paginación:** page/pageSize, limit/offset, metadatos de paginación
   - **Filtros:** Por nombre, tipo de documento, documento, estado, email/phone
   - **Búsqueda rápida:** Parámetro q para búsqueda general
   - **Ordenamiento:** Parámetro sort con order
   - **Validación de seguridad:** Protección contra inyección SQL en filtros

3. **Recomendaciones de Implementación:**
   - Implementar paginación usando Django REST Framework's `PageNumberPagination` o `LimitOffsetPagination`
   - Agregar filtrado usando `django_filters` o filtros personalizados en el ViewSet
   - Implementar búsqueda con SearchFilter de DRF
   - Agregar ordenamiento con OrderingFilter de DRF
   - Validar y sanear parámetros de consulta para prevenir inyección SQL

4. **Estado del Endpoint:** El endpoint está **OPERATIVO** para listado básico pero requiere mejoras para cumplir con todos los requisitos funcionales de HU-CLI-002.

5. **Pruebas de Integración:** Se recomienda:
   - Ejecutar pruebas contra la base de datos PostgreSQL real con volumen de datos significativo
   - Realizar pruebas de carga para verificar rendimiento con 1000+ clientes
   - Validar integración con el microservicio de usuarios para el campo "Usuario Activo"

---

**Documento generado automáticamente por el sistema de pruebas UT-CLI-002**  
**Versión:** 1.0  
**Última actualización:** Octubre 11, 2025
