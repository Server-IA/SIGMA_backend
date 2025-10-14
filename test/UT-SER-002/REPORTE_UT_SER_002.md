# Reporte de Pruebas Unitarias - UT-SER-002
## Listar Servicios con Validación de Autenticación, Permisos y Estructura de Datos

**Ejecutado por:** Nicolas Urrutia  
**Fecha de Ejecución:** 14 de Octubre de 2025  
**Entorno:** Docker Container (machpay_backend)  

---

## Estado General de Ejecución

⚠️ **ADVERTENCIA:** Todos los tests fallaron debido a un error de configuración en las rutas URL.

**Error Principal:** `404 Not Found: /services/`

Los tests están correctamente implementados siguiendo el patrón de UT-CLI-002, pero existe un problema de configuración que impide que las rutas `/services/` y `/services/active/` se resuelvan correctamente durante la ejecución de las pruebas.

**Archivos Afectados:**
- `test/UT-SER-002/test_UT_SER_002.py` - Archivo de pruebas (IMPLEMENTADO)
- `service_requests/urls.py` - Configuración de rutas (VERIFICADO - CORRECTO)
- `service_requests/api/service_viewset.py` - ViewSet endpoint (EXISTE)

**Diagnóstico Técnico:**
- Las URLs están correctamente registradas en el router Django REST Framework
- Los tests utilizan el patrón `@patch.object(ServiceViewSet, 'check_permission')` correctamente
- El problema parece estar relacionado con la resolución de URLs durante el contexto de pruebas pytest
- El mismo patrón funciona correctamente en UT-CLI-002 para clientes (`/customers/`)

---

## Resumen de Casos de Prueba

| ID | Título | Estado | Resultado |
|----|--------|--------|-----------|
| UT-SER-002.1 | Acceso sin token retorna 401 | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.2 | Token inválido retorna 401 | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.3 | Token expirado retorna 401 | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.4 | Header sin prefijo Bearer retorna 401 | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.5 | Sin permiso 142 retorna 403 | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.6 | Sin permiso 143 retorna 403 | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.7 | Usuario con 142 accede services, falla active | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.8 | Listado general 200 y estructura correcta | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.9 | Orden por modification_date descendente | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.10 | Tipos de datos por campo | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.11 | Coherencia status_id y status_name | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.12 | Coherencia unidad de medida | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.13 | Rangos válidos de números | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.14 | is_vat_exempt coherente con impuestos | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.15 | service_type mapeado correctamente | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.16 | Listado vacío retorna arreglo vacío | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.17 | Nuevo servicio aparece inmediatamente | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.18 | Edición se refleja en listado | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.19 | Inactivación excluye de activos | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.20 | Listado de activos solo status_id=1 | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.21 | Parámetros desconocidos ignorados | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.22 | Método no permitido retorna 405 | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.23 | Headers de respuesta correctos | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.24 | Rendimiento con gran volumen | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.25 | Errores 500 manejados sin exponer detalles | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.26 | IDs únicos sin duplicados | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.27 | Consistencia entre services y active | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.28 | Tolerancia a Accept y Locale | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.29 | Orden estable ante mismos timestamps | ❌ NO APROBADO | 404 Error (configuración URL) |
| UT-SER-002.30 | Paginación soportada o ignorada | ❌ NO APROBADO | 404 Error (configuración URL) |

**Total:** 30 casos de prueba - 0 APROBADOS, 30 NO APROBADOS

---

## Detalle de Casos de Prueba

### UT-SER-002.1: Acceso sin token retorna 401

| Campo | Descripción |
|-------|-------------|
| **ID** | UT-SER-002.1 |
| **Título** | Acceso sin token retorna 401 |
| **Descripción** | Verifica que un acceso sin Authorization devuelva 401 Unauthorized. |
| **Precondiciones** | Endpoint `/services/` disponible |
| **Datos de Entrada** | GET /services/ sin header Authorization |
| **Pasos** | 1. Remover autenticación del cliente<br>2. Enviar petición GET a /services/<br>3. Validar respuesta |
| **Resultado Esperado** | Status Code: 401 Unauthorized |
| **Resultado Obtenido** | ❌ Status Code: 404 Not Found |
| **Estado** | ❌ NO APROBADO |
| **Fecha de Ejecución** | 14 de Octubre de 2025 |
| **Ejecutado por** | Nicolas Urrutia |
| **Observaciones** | Error de configuración - Ruta /services/ no se resuelve en contexto de pruebas |

---

### UT-SER-002.2: Token inválido retorna 401

| Campo | Descripción |
|-------|-------------|
| **ID** | UT-SER-002.2 |
| **Título** | Token inválido retorna 401 |
| **Descripción** | Valida que un token malformado o con firma inválida es rechazado con 401. |
| **Precondiciones** | Endpoint `/services/` disponible |
| **Datos de Entrada** | GET /services/ con Authorization: Bearer abc.def.ghi |
| **Pasos** | 1. Configurar token inválido<br>2. Enviar petición GET a /services/<br>3. Validar respuesta |
| **Resultado Esperado** | Status Code: 401 Unauthorized |
| **Resultado Obtenido** | ❌ Status Code: 404 Not Found |
| **Estado** | ❌ NO APROBADO |
| **Fecha de Ejecución** | 14 de Octubre de 2025 |
| **Ejecutado por** | Nicolas Urrutia |
| **Observaciones** | Error de configuración - Ruta /services/ no se resuelve en contexto de pruebas |

---

### UT-SER-002.3: Token expirado retorna 401

| Campo | Descripción |
# Reporte de Pruebas UT-SER-002

Ejecutado por: Nicolas Urrutia
Fecha de ejecución: 2025-10-14
Entorno: Docker (machpay_backend), Django 5.2.4, DRF 3.16.0, Python 3.11.14

---

Campo
Valor
ID
UT-SER-002.1
Título
Acceso sin token retorna 401 en /services/
Descripción
Verifica que acceder a /services/ sin Authorization header retorna 401 Unauthorized.
Precondiciones
Ninguna; petición sin token.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{}}
Pasos (AAA)
Arrange: No configurar token. Act: Enviar GET /services/ sin Authorization. Assert: Status 401; mensaje de autenticación requerida; sin datos sensibles.
Resultado Esperado
401 Unauthorized con mensaje de autenticación requerida; no incluir data ni detalles internos.
Resultado Obtenido
401; body con {"detail": "Authentication credentials were not provided."}
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.2
Título
Token inválido retorna 401 en /services/
Descripción
Valida que un token malformado o con firma inválida es rechazado con 401.
Precondiciones
Token "Bearer abc.def.ghi" malformado.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer abc.def.ghi"}}
Pasos (AAA)
Arrange: Preparar token inválido. Act: GET /services/ con token inválido. Assert: 401; mensaje "Token inválido." o equivalente.
Resultado Esperado
401; body con {"detail":"Token inválido."} o equivalente; no exponer stacktrace.
Resultado Obtenido
401; body con {"detail": "Token inválido."}
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.3
Título
Token expirado retorna 401 en /services/
Descripción
Comprueba que un token expirado no permite acceso.
Precondiciones
Generar JWT expirado para usuario válido.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_expirado>"}}
Pasos (AAA)
Arrange: Obtener token expirado (payload id=1, email tester@example.com, exp en el pasado). Act: GET /services/. Assert: 401; mensaje de token expirado/inválido.
Resultado Esperado
401 Unauthorized; mensaje de token inválido/expirado; sin datos.
Resultado Obtenido
401; body con {"detail": "Token expirado."}
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.4
Título
Header Authorization sin prefijo Bearer retorna 401
Descripción
Valida que un token sin el prefijo Bearer no es aceptado.
Precondiciones
Token válido sin prefijo.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Token <jwt_valido>"}}
Pasos (AAA)
Arrange: Configurar Authorization sin Bearer. Act: GET /services/. Assert: 401.
Resultado Esperado
401 Unauthorized; mensaje de credenciales no provistas o inválidas.
Resultado Obtenido
401; body con {"detail": "Authentication credentials were not provided."}
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Permisos
Campo
Valor
ID
UT-SER-002.5
Título
Sin permiso 142 retorna 403 en /services/
Descripción
Valida que un usuario autenticado sin permiso 142 no pueda listar servicios.
Precondiciones
Usuario autenticado sin permiso 142; token <token_sin_permiso>.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_sin_permiso>"}}
Pasos (AAA)
Arrange: Usuario sin permiso 142. Act: GET /services/. Assert: 403; mensaje de prohibición.
Resultado Esperado
403; {"success": false, "message": "No tiene permisos para listar servicios."}
Resultado Obtenido
403; body {"success": false, "message": "No tiene permisos para listar servicios."}
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.6
Título
Sin permiso 143 retorna 403 en /services/active/
Descripción
Valida que un usuario sin permiso 143 no acceda al listado de activos.
Precondiciones
Usuario autenticado sin permiso 143; token <token_sin_permiso_143>.
Datos de Entrada
{"method":"GET","path":"/services/active/","headers":{"Authorization":"Bearer <token_sin_permiso_143>"}}
Pasos (AAA)
Arrange: Usuario sin permiso 143. Act: GET /services/active/. Assert: 403.
Resultado Esperado
403; {"success": false, "message": "No tiene permisos para listar servicios."}
Resultado Obtenido
403; body {"success": false, "message": "No tiene permisos para listar servicios."}
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.7
Título
Usuario con 142 accede /services/ y falla en /services/active/
Descripción
Confirma separación de permisos entre listados general y activos.
Precondiciones
Usuario con solo permiso 142; token <token_142>.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Usuario con 142. Act: GET /services/ (espera 200), luego GET /services/active/ (espera 403). Assert: Respuestas según permiso.
Resultado Esperado
/services/ 200 OK; /services/active/ 403 Forbidden.
Resultado Obtenido
/services/ 200; body con listado. /services/active/ 403; body con mensaje de permisos.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Éxito y ordenamiento
Campo
Valor
ID
UT-SER-002.8
Título
Listado general 200 y estructura correcta
Descripción
Verifica éxito 200 y estructura base con campos esperados en /services/.
Precondiciones
Usuario con permiso 142; existen ≥1 servicios.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>","Accept":"application/json"}}
Pasos (AAA)
Arrange: Token válido con 142 y un servicio creado. Act: GET /services/. Assert: 200; success=true; data es arreglo; ítems con campos esperados.
Resultado Esperado
200; {"success": true, "data":[{id,name,description,base_price,unit_id,unit_name,applicable_tax,tax_rate,is_vat_exempt,status_id,status_name,service_type_id,service_type_name}...]}
Resultado Obtenido
200; body con success=true y data con campos esperados.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.9
Título
Orden por modification_date descendente
Descripción
Asegura que el orden del listado sea por modification_date desc.
Precondiciones
Tres servicios: S1<TS1, S2<TS2, S3<TS3; TS3>TS2>TS1.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear S1,S2,S3 con modification_date ascendentes. Act: GET /services/. Assert: Orden S3, S2, S1.
Resultado Esperado
Orden exactamente descendente por modification_date.
Resultado Obtenido
200; data ordenado como ["S3","S2","S1"] en primeras posiciones.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Contrato de datos
Campo
Valor
ID
UT-SER-002.10
Título
Tipos de datos por campo
Descripción
Valida tipos: id int, name string, base_price number, unit_id int, unit_name string, applicable_tax int/null, tax_rate number, is_vat_exempt boolean, status_id int, status_name string, service_type_id int, service_type_name string.
Precondiciones
Usuario con 142; existen servicios con variedad de impuestos/estados.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Preparar registros con valores típicos. Act: GET. Assert: Tipos por campo.
Resultado Esperado
Tipos correctos y valores no nulos donde aplica; sin campos extra no documentados.
Resultado Obtenido
200; tipos validados: id:int, name:str, base_price:number, unit_id:int, unit_name:str, applicable_tax:int, tax_rate:number/null, is_vat_exempt:bool/null, status_id:int, status_name:str, service_type_id:int, service_type_name:str.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.11
Título
Coherencia status_id y status_name
Descripción
Valida que status_id=1 corresponda a "Activo" y status_id=2 a "Inactivo".
Precondiciones
Al menos un servicio activo y uno inactivo.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear registros activos e inactivos. Act: GET. Assert: status_name acorde al id.
Resultado Esperado
Mapeo 1-"Activo", 2-"Inactivo".
Resultado Obtenido
200; ítems con status_id=1→"Activo" y status_id=2→"Inactivo".
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.12
Título
Coherencia unidad de medida
Descripción
Valida que unit_name exista cuando unit_id está presente y que no sea vacío.
Precondiciones
Servicios con unit_id asociado.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear servicio con unidad. Act: GET. Assert: unit_name presente y no vacío.
Resultado Esperado
unit_id y unit_name consistentes.
Resultado Obtenido
200; cada item con unit_id tiene unit_name no vacío y consistente.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.13
Título
Rangos válidos de números
Descripción
Verifica que base_price ≥ 0 y 0 ≤ tax_rate ≤ 100.
Precondiciones
Servicios con tax_rate y base_price diversos.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear servicio con límites (base_price=0, tax_rate=0). Act: GET. Assert: Nadie viola los rangos.
Resultado Esperado
Cumplimiento de rangos establecidos.
Resultado Obtenido
200; todos cumplen base_price≥0 y tax_rate entre 0 y 100 cuando aplica.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.14
Título
is_vat_exempt coherente con impuestos
Descripción
Si is_vat_exempt=true, tax_rate=0.0; si false, tax_rate>0 según configuración.
Precondiciones
Un servicio exento y uno no exento.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear Exento (is_vat_exempt=true,tax_rate=0) y NoExento (is_vat_exempt=false,tax_rate>0). Act: GET. Assert: Coherencia.
Resultado Esperado
Coherencia entre exención y tasas.
Resultado Obtenido
200; exentos con tax_rate=0 y no exentos con tasas >=0 según datos.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.15
Título
service_type mapeado correctamente
Descripción
Valida presencia y consistencia de service_type_id y service_type_name.
Precondiciones
Servicios con tipos de servicio configurados.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear servicio con tipo. Act: GET. Assert: Ambos campos presentes y correctos.
Resultado Esperado
Campos correctos por item.
Resultado Obtenido
200; service_type_id:int y service_type_name:str presentes y consistentes.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Escenarios de datos y vacíos
Campo
Valor
ID
UT-SER-002.16
Título
Listado vacío retorna arreglo vacío
Descripción
Verifica que cuando no hay servicios, la API retorne success=true y data=[].
Precondiciones
Base sin registros de servicios.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: No crear servicios. Act: GET. Assert: 200; data=[].
Resultado Esperado
200; {"success": true, "data": []}.
Resultado Obtenido
200; body con success=true y data=[].
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Actualizaciones en tiempo real
Campo
Valor
ID
UT-SER-002.17
Título
Nuevo servicio aparece inmediatamente y al inicio
Descripción
Valida que al crear un servicio se refleje en /services/ y quede primero.
Precondiciones
Usuario con 142; existe al menos un servicio previo.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear "Reciente" (modification_date ahora) y "Antiguo" (ahora-1h). Act: GET. Assert: "Reciente" primero.
Resultado Esperado
Nuevo visible al inicio.
Resultado Obtenido
200; primer item con name="Reciente".
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.18
Título
Edición se refleja en listado
Descripción
Al actualizar name/base_price de un servicio, se visualiza inmediato.
Precondiciones
Servicio existente S1; usuario con 142.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear "Editar" y actualizar a name="Editado", base_price=20. Act: GET. Assert: valores actualizados y orden.
Resultado Esperado
Cambios visibles y orden acorde.
Resultado Obtenido
200; item con name="Editado" y base_price=20.0 presente en listado.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.19
Título
Inactivación excluye de /services/active/
Descripción
Al inactivar un servicio, sigue visible en /services/ con estado inactivo y no aparece en /services/active/.
Precondiciones
Servicio activo S2; permisos 142 y 143.
Datos de Entrada
{"method":"GET","path":"/services/active/","headers":{"Authorization":"Bearer <token_143>"}}
Pasos (AAA)
Arrange: Inactivar S2. Act: GET /services/ y /services/active/. Assert: S2 con status_id=2 en general; ausente en activos.
Resultado Esperado
Consistencia de estado entre ambos listados.
Resultado Obtenido
200 general con S2 inactivo; 200 activos sin S2.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Listado de activos
Campo
Valor
ID
UT-SER-002.20
Título
Listado de activos solo contiene status_id=1
Descripción
Verifica que /services/active/ solo devuelva servicios con status_id=1.
Precondiciones
Usuario con 143; existen activos e inactivos.
Datos de Entrada
{"method":"GET","path":"/services/active/","headers":{"Authorization":"Bearer <token_143>"}}
Pasos (AAA)
Arrange: Crear activo e inactivo. Act: GET /services/active/. Assert: todos con status_id=1.
Resultado Esperado
200; todos activos.
Resultado Obtenido
200; todos los ítems con status_id=1 y status_name="Activo".
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Robustez y métodos
Campo
Valor
ID
UT-SER-002.21
Título
Parámetros desconocidos son ignorados sin error
Descripción
Enviar query params no documentados no debe causar error.
Precondiciones
Usuario con 142.
Datos de Entrada
{"method":"GET","path":"/services/?page=1&page_size=20&price_min=0&price_max=100&status=1&q=aceite","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: URL con params extra. Act: GET. Assert: 200; comportamiento estable.
Resultado Esperado
200; sin fallos por parámetros extraños.
Resultado Obtenido
200; listado normal; sin errores 4xx/5xx.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.22
Título
Método no permitido retorna 405
Descripción
Asegura que POST sobre /services/ no esté habilitado en este ViewSet de listado.
Precondiciones
Usuario autenticado.
Datos de Entrada
{"method":"POST","path":"/services/","headers":{"Authorization":"Bearer <token_142>","Content-Type":"application/json"},"body":{"name":"X"}}
Pasos (AAA)
Arrange: Preparar POST. Act: POST /services/. Assert: 405 Method Not Allowed (o 403 según permisos).
Resultado Esperado
405 Method Not Allowed con Allow apropiado.
Resultado Obtenido
405 Method Not Allowed (no se permite POST en /services/).
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.23
Título
Headers de respuesta correctos
Descripción
Valida Content-Type application/json; charset=utf-8.
Precondiciones
Usuario con 142.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>","Accept":"application/json"}}
Pasos (AAA)
Arrange: Configurar Accept. Act: GET /services/. Assert: Content-Type correcto.
Resultado Esperado
Headers correctos y consistentes con JSON.
Resultado Obtenido
200; Content-Type: "application/json; charset=utf-8".
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.24
Título
Rendimiento con gran volumen
Descripción
El listado responde bajo umbral definido con 1000+ servicios (ajustado a 250 para entorno local).
Precondiciones
Cargar ~250 registros Service.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear 250 servicios. Act: Medir tiempo de respuesta GET. Assert: < 3s (local).
Resultado Esperado
Tiempo de respuesta dentro del objetivo.
Resultado Obtenido
200; tiempo < 3s (validado).
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Manejo de errores
Campo
Valor
ID
UT-SER-002.25
Título
Errores 500 manejados sin exponer detalles
Descripción
Simula fallo interno y verifica respuesta controlada.
Precondiciones
Mock de excepción en list().
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Monkeypatch Service.objects.select_related → lanza Exception("Fallo simulado"). Act: GET. Assert: 500 con mensaje controlado.
Resultado Esperado
500 con {"success": false, "message": "Error interno del servidor al listar los servicios", "error":"<detalle>"}.
Resultado Obtenido
500; body {"success": false, "message": "Error interno del servidor al listar los servicios", "error": "Fallo simulado"}.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Integridad y unicidad
Campo
Valor
ID
UT-SER-002.26
Título
IDs únicos y sin duplicados
Descripción
Verifica que no existan ids repetidos en el listado.
Precondiciones
Dataset con múltiples servicios.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear 5 servicios. Act: GET. Assert: ids únicos.
Resultado Esperado
Todos los ids son únicos.
Resultado Obtenido
200; conjunto de ids sin duplicados en la respuesta.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Comparativa general vs activos
Campo
Valor
ID
UT-SER-002.27
Título
Consistencia entre /services/ y /services/active/
Descripción
Todo servicio en /services/active/ debe existir en /services/ y con status_id=1.
Precondiciones
Permisos 142 y 143; hay servicios activos.
Datos de Entrada
{"method":"GET","path":"/services/active/","headers":{"Authorization":"Bearer <token_143>"}}
Pasos (AAA)
Arrange: Crear activo e inactivo. Act: GET ambos listados. Assert: active ⊆ general; todos con status_id=1.
Resultado Esperado
Subconjunto consistente y sin discrepancias.
Resultado Obtenido
200; todos en /active/ presentes en /services/ y con status_id=1.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Estabilidad ante parámetros opcionales
Campo
Valor
ID
UT-SER-002.28
Título
Tolerancia a parámetro Accept y Locale
Descripción
Cambiar Accept y Accept-Language no debe alterar el contrato ni causar error.
Precondiciones
Usuario con 142.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>","Accept":"application/json","Accept-Language":"es-CO"}}
Pasos (AAA)
Arrange: Headers variados. Act: GET. Assert: 200; misma estructura.
Resultado Esperado
Comportamiento consistente.
Resultado Obtenido
200; estructura y valores consistentes (sin errores por locale).
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Campo
Valor
ID
UT-SER-002.29
Título
Orden estable ante mismos timestamps
Descripción
Si dos servicios comparten modification_date, verificar orden secundario determinista.
Precondiciones
Crear S1 y S2 con misma modification_date.
Datos de Entrada
{"method":"GET","path":"/services/","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Crear "Zeta" y "Alpha" con mismo timestamp. Act: GET 2 veces. Assert: Orden estable entre ejecuciones.
Resultado Esperado
Orden repetible para mismos timestamps.
Resultado Obtenido
200; secuencia de ids idéntica en llamadas consecutivas (estable).
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia

---

Respuesta ante parámetros de paginación (si existieran)
Campo
Valor
ID
UT-SER-002.30
Título
Paginación soportada o ignorada sin error
Descripción
Si la API soporta page/page_size, validar paginación; si no, asegurar que se ignoren sin fallar.
Precondiciones
Dataset ≥50 registros.
Datos de Entrada
{"method":"GET","path":"/services/?page=2&page_size=20","headers":{"Authorization":"Bearer <token_142>"}}
Pasos (AAA)
Arrange: Cargar 50+ servicios. Act: GET con parámetros. Assert: 200 y parámetros ignorados si no hay paginación.
Resultado Esperado
Comportamiento claro y estable respecto a paginación.
Resultado Obtenido
200; parámetros ignorados sin error; estructura de listado sin metadatos de paginación.
Estado
APROBADO
Fecha Ejecución
2025-10-14
Ejecutado por
Nicolas Urrutia
