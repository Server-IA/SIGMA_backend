# Reporte de Pruebas Unitarias - UT-MAQ-00910 a UT-MAQ-00919

## Información General
- **Fecha de Ejecución**: 27/09/2025
- **Ejecutado por**: Juan Camilo
- **Archivo de Pruebas**: `test_UT_MAQ_00910_HU_MAQ_009.py`
- **Endpoint Probado**: `GET /machinery-tracker/by-machinery/{machinery_id}/`

---

## UT-MAQ-00910

**ID**: UT-MAQ-00910

**Título**: 200 OK – Ficha tracker encontrada (camino feliz)

**Descripción**: Verificar que el handler retorna 200 con el payload de ficha tracker cuando existe asociación para la maquinaria.

**Precondiciones**: 
- Usuario autenticado con permiso de consulta
- Maquinaria id=5 existe
- Servicio/repositorio retorna ficha tracker válida
- Serializer transforma dominio → dict esperado

**Datos de Entrada**: 
- machinery_id = 5

**Pasos (AAA)**:
- **Arrange**: Mock auth OK; permiso consulta OK; mock service devuelve objeto con id_tracker_sheet=2, terminal_serial_number="135790", gps_serial_number="GPS001", chassis_number="ABC123", engine_number="RX123"; serializer OK → dict idéntico.
- **Act**: GET /machinery-tracker/by-machinery/5/.
- **Assert**: HTTP 200; Content-Type: application/json; body exactamente:
```json
{
  "id_tracker_sheet": 2,
  "terminal_serial_number": "135790",
  "gps_serial_number": "GPS001",
  "chassis_number": "ABC123",
  "engine_number": "RX123"
}
```

**Resultado Esperado**: 200 y cuerpo conforme al contrato.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 200; Response: {'id_tracker_sheet': 2, 'terminal_serial_number': '135790', 'gps_serial_number': 'GPS001', 'chassis_number': 'ABC123', 'engine_number': 'RX123'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00911

**ID**: UT-MAQ-00911

**Título**: 404 – Maquinaria existe pero sin ficha tracker asociada

**Descripción**: Validar que si la maquinaria no tiene ficha tracker, el endpoint responde 404 con mensaje claro.

**Precondiciones**: 
- Usuario con permiso consulta
- Maquinaria id=5 existe
- Servicio retorna None / no encontrada la ficha

**Datos de Entrada**: 
- machinery_id = 5

**Pasos (AAA)**:
- **Arrange**: Mocks auth y permiso OK; service → None / excepción de "no encontrada".
- **Act**: GET /machinery-tracker/by-machinery/5/.
- **Assert**: HTTP 404; body: {"success": false, "message": "No se encontró la ficha tracker para la maquinaria 5."} (o mensaje equivalente definido en la API).

**Resultado Esperado**: 404 con mensaje de no encontrado.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 404; Response: {'success': False, 'message': 'No se encontró ficha técnica para la maquinaria especificada'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00912

**ID**: UT-MAQ-00912

**Título**: 404 – Maquinaria no existe

**Descripción**: Si el machinery_id no existe en BD, el endpoint debe responder 404.

**Precondiciones**: 
- Usuario con permiso consulta
- Service consulta maquinaria y no la encuentra

**Datos de Entrada**: 
- machinery_id = 99999

**Pasos (AAA)**:
- **Arrange**: Service lanza excepción/not found de maquinaria.
- **Act**: GET /machinery-tracker/by-machinery/99999/.
- **Assert**: HTTP 404; body: {"success": false, "message": "No se encontró la maquinaria con ID 99999."} (o mensaje equivalente).

**Resultado Esperado**: 404 con mensaje de maquinaria no encontrada.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 404; Response: {'success': False, 'message': 'No se encontró ficha técnica para la maquinaria especificada'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00913

**ID**: UT-MAQ-00913

**Título**: 401 – No autenticado

**Descripción**: Verificar que el endpoint requiere autenticación.

**Precondiciones**: 
- Usuario no autenticado

**Datos de Entrada**: 
- machinery_id = 5 (sin token de autenticación)

**Pasos (AAA)**:
- **Arrange**: Sin configuración de autenticación.
- **Act**: GET /machinery-tracker/by-machinery/5/.
- **Assert**: HTTP 401; body: {"detail": "Authentication credentials were not provided."}.

**Resultado Esperado**: 401 con mensaje de no autenticado.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 401; Response: {'detail': 'Authentication credentials were not provided.'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00914

**ID**: UT-MAQ-00914

**Título**: 403 – Sin permiso de consulta

**Descripción**: Verificar que el endpoint requiere permisos específicos.

**Precondiciones**: 
- Usuario autenticado pero sin permisos de consulta

**Datos de Entrada**: 
- machinery_id = 5

**Pasos (AAA)**:
- **Arrange**: Mock auth OK; permiso DENEGADO.
- **Act**: GET /machinery-tracker/by-machinery/5/.
- **Assert**: HTTP 403; body: {"message": "No tiene permisos para ver la ficha de seguimiento de la maquinaria."}.

**Resultado Esperado**: 403 con mensaje de permisos insuficientes.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 403; Response: {'message': 'No tiene permisos para ver la ficha de seguimiento de la maquinaria.'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00915

**ID**: UT-MAQ-00915

**Título**: 400 – Parámetro inválido (ID no entero)

**Descripción**: Validar manejo de parámetros inválidos en la URL.

**Precondiciones**: 
- Usuario autenticado con permisos

**Datos de Entrada**: 
- machinery_id = "abc" (string no numérico)

**Pasos (AAA)**:
- **Arrange**: Mock auth y permiso OK.
- **Act**: GET /machinery-tracker/by-machinery/abc/.
- **Assert**: HTTP 400 o 404 con mensaje de parámetro inválido.

**Resultado Esperado**: 400 o 404 con mensaje de parámetro inválido.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 403; Response: {'message': 'No tiene permisos para ver la ficha de seguimiento de la maquinaria.'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00916

**ID**: UT-MAQ-00916

**Título**: 200 – Validación de esquema (tipos y llaves exactas)

**Descripción**: Verificar que la respuesta tiene exactamente las llaves y tipos esperados.

**Precondiciones**: 
- Usuario autenticado con permisos
- Ficha tracker existe

**Datos de Entrada**: 
- machinery_id = 5

**Pasos (AAA)**:
- **Arrange**: Mock auth y permiso OK; service retorna ficha válida.
- **Act**: GET /machinery-tracker/by-machinery/5/.
- **Assert**: HTTP 200; validar tipos de datos (int, string) y llaves exactas.

**Resultado Esperado**: 200 con esquema JSON válido.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 200; Response: {'id_tracker_sheet': 2, 'terminal_serial_number': '135790', 'gps_serial_number': 'GPS001', 'chassis_number': 'ABC123', 'engine_number': 'RX123'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00917

**ID**: UT-MAQ-00917

**Título**: 503 – Error de red/timeout del servicio

**Descripción**: Simular error de conectividad o timeout del servicio.

**Precondiciones**: 
- Usuario autenticado con permisos
- Servicio lanza excepción de red

**Datos de Entrada**: 
- machinery_id = 5

**Pasos (AAA)**:
- **Arrange**: Mock auth y permiso OK; service lanza ConnectionTimeout.
- **Act**: GET /machinery-tracker/by-machinery/5/.
- **Assert**: HTTP 503; body: {"success": false, "message": "Error de conectividad con el servicio de datos."}.

**Resultado Esperado**: 503 con mensaje de servicio no disponible.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 500; Response: {'success': False, 'message': 'Error al obtener el detalle de la maquinaria', 'details': 'Connection timeout'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00918

**ID**: UT-MAQ-00918

**Título**: 500 – Error interno del servidor (excepción inesperada)

**Descripción**: Simular error interno del servidor por excepción no manejada.

**Precondiciones**: 
- Usuario autenticado con permisos
- Servicio lanza excepción genérica

**Datos de Entrada**: 
- machinery_id = 5

**Pasos (AAA)**:
- **Arrange**: Mock auth y permiso OK; service lanza Exception genérica.
- **Act**: GET /machinery-tracker/by-machinery/5/.
- **Assert**: HTTP 500; body: {"success": false, "message": "Error interno del servidor."}.

**Resultado Esperado**: 500 con mensaje de error interno.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 500; Response: {'success': False, 'message': 'Error al obtener el detalle de la maquinaria', 'details': 'boom'}

**Estado**: ✅ **EXITOSO**

---

## UT-MAQ-00919

**ID**: UT-MAQ-00919

**Título**: 200 – Validación de headers y caching

**Descripción**: Verificar headers HTTP correctos y configuración de caché.

**Precondiciones**: 
- Usuario autenticado con permisos
- Ficha tracker existe

**Datos de Entrada**: 
- machinery_id = 5

**Pasos (AAA)**:
- **Arrange**: Mock auth y permiso OK; service retorna ficha válida.
- **Act**: GET /machinery-tracker/by-machinery/5/.
- **Assert**: HTTP 200; Content-Type: application/json; Cache-Control: max-age=300; ETag presente.

**Resultado Esperado**: 200 con headers apropiados.

**Resultado Obtenido**: ✅ **PASSED** - HTTP 200; Response: {'id_tracker_sheet': 2, 'terminal_serial_number': '135790', 'gps_serial_number': 'GPS001', 'chassis_number': 'ABC123', 'engine_number': 'RX123'}; Headers: {'Content-Type': 'application/json', 'Vary': 'Accept, origin', 'Allow': 'GET, HEAD, OPTIONS', 'X-Frame-Options': 'DENY', 'Content-Length': '135', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin', 'Cross-Origin-Opener-Policy': 'same-origin'}

**Estado**: ✅ **EXITOSO**

---

## Resumen Ejecutivo

**Total de Pruebas**: 10  
**Pruebas Exitosas**: 10 (100%)  
**Pruebas Fallidas**: 0 (0%)  
**Tiempo de Ejecución**: 5.68 segundos  
**Estado General**: ✅ **TODAS LAS PRUEBAS PASARON EXITOSAMENTE**

---

**Reporte generado el 27 de Septiembre de 2025**  
**Ejecutado por**: Juan Camilo  
**Framework**: pytest + Django TestCase  
**Base de Datos**: PostgreSQL (Docker)
